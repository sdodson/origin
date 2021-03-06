package testsuites

import (
	"bytes"
	"crypto/sha1"
	"io"
	"io/ioutil"
	"math/rand"
	"net/http"
	"os"
	"path"
	"sort"
	"sync"
	"testing"
	"time"

	storagedriver "github.com/docker/distribution/registry/storage/driver"

	"gopkg.in/check.v1"
)

// Test hooks up gocheck into the "go test" runner.
func Test(t *testing.T) { check.TestingT(t) }

// RegisterInProcessSuite registers an in-process storage driver test suite with
// the go test runner.
func RegisterInProcessSuite(driverConstructor DriverConstructor, skipCheck SkipCheck) {
	check.Suite(&DriverSuite{
		Constructor: driverConstructor,
		SkipCheck:   skipCheck,
	})
}

// RegisterIPCSuite registers a storage driver test suite which runs the named
// driver as a child process with the given parameters.
func RegisterIPCSuite(driverName string, ipcParams map[string]string, skipCheck SkipCheck) {
	panic("ipc testing is disabled for now")

	// NOTE(stevvooe): IPC testing is disabled for now. Uncomment the code
	// block before and remove the panic when we phase it back in.

	// suite := &DriverSuite{
	// 	Constructor: func() (storagedriver.StorageDriver, error) {
	// 		d, err := ipc.NewDriverClient(driverName, ipcParams)
	// 		if err != nil {
	// 			return nil, err
	// 		}
	// 		err = d.Start()
	// 		if err != nil {
	// 			return nil, err
	// 		}
	// 		return d, nil
	// 	},
	// 	SkipCheck: skipCheck,
	// }
	// suite.Teardown = func() error {
	// 	if suite.StorageDriver == nil {
	// 		return nil
	// 	}

	// 	driverClient := suite.StorageDriver.(*ipc.StorageDriverClient)
	// 	return driverClient.Stop()
	// }
	// check.Suite(suite)
}

// SkipCheck is a function used to determine if a test suite should be skipped.
// If a SkipCheck returns a non-empty skip reason, the suite is skipped with
// the given reason.
type SkipCheck func() (reason string)

// NeverSkip is a default SkipCheck which never skips the suite.
var NeverSkip SkipCheck = func() string { return "" }

// DriverConstructor is a function which returns a new
// storagedriver.StorageDriver.
type DriverConstructor func() (storagedriver.StorageDriver, error)

// DriverTeardown is a function which cleans up a suite's
// storagedriver.StorageDriver.
type DriverTeardown func() error

// DriverSuite is a gocheck test suite designed to test a
// storagedriver.StorageDriver.
// The intended way to create a DriverSuite is with RegisterInProcessSuite or
// RegisterIPCSuite.
type DriverSuite struct {
	Constructor DriverConstructor
	Teardown    DriverTeardown
	SkipCheck
	storagedriver.StorageDriver
}

// SetUpSuite sets up the gocheck test suite.
func (suite *DriverSuite) SetUpSuite(c *check.C) {
	if reason := suite.SkipCheck(); reason != "" {
		c.Skip(reason)
	}
	d, err := suite.Constructor()
	c.Assert(err, check.IsNil)
	suite.StorageDriver = d
}

// TearDownSuite tears down the gocheck test suite.
func (suite *DriverSuite) TearDownSuite(c *check.C) {
	if suite.Teardown != nil {
		err := suite.Teardown()
		c.Assert(err, check.IsNil)
	}
}

// TearDownTest tears down the gocheck test.
// This causes the suite to abort if any files are left around in the storage
// driver.
func (suite *DriverSuite) TearDownTest(c *check.C) {
	files, _ := suite.StorageDriver.List("/")
	if len(files) > 0 {
		c.Fatalf("Storage driver did not clean up properly. Offending files: %#v", files)
	}
}

// TestValidPaths checks that various valid file paths are accepted by the
// storage driver.
func (suite *DriverSuite) TestValidPaths(c *check.C) {
	contents := randomContents(64)
	validFiles := []string{
		"/a",
		"/2",
		"/aa",
		"/a.a",
		"/0-9/abcdefg",
		"/abcdefg/z.75",
		"/abc/1.2.3.4.5-6_zyx/123.z/4",
		"/docker/docker-registry",
		"/123.abc",
		"/abc./abc",
		"/.abc",
		"/a--b",
		"/a-.b",
		"/_.abc"}

	for _, filename := range validFiles {
		err := suite.StorageDriver.PutContent(filename, contents)
		defer suite.StorageDriver.Delete(firstPart(filename))
		c.Assert(err, check.IsNil)

		received, err := suite.StorageDriver.GetContent(filename)
		c.Assert(err, check.IsNil)
		c.Assert(received, check.DeepEquals, contents)
	}
}

// TestInvalidPaths checks that various invalid file paths are rejected by the
// storage driver.
func (suite *DriverSuite) TestInvalidPaths(c *check.C) {
	contents := randomContents(64)
	invalidFiles := []string{
		"",
		"/",
		"abc",
		"123.abc",
		"//bcd",
		"/abc_123/",
		"/Docker/docker-registry"}

	for _, filename := range invalidFiles {
		err := suite.StorageDriver.PutContent(filename, contents)
		defer suite.StorageDriver.Delete(firstPart(filename))
		c.Assert(err, check.NotNil)
		c.Assert(err, check.FitsTypeOf, storagedriver.InvalidPathError{})

		_, err = suite.StorageDriver.GetContent(filename)
		c.Assert(err, check.NotNil)
		c.Assert(err, check.FitsTypeOf, storagedriver.InvalidPathError{})
	}
}

// TestWriteRead1 tests a simple write-read workflow.
func (suite *DriverSuite) TestWriteRead1(c *check.C) {
	filename := randomPath(32)
	contents := []byte("a")
	suite.writeReadCompare(c, filename, contents)
}

// TestWriteRead2 tests a simple write-read workflow with unicode data.
func (suite *DriverSuite) TestWriteRead2(c *check.C) {
	filename := randomPath(32)
	contents := []byte("\xc3\x9f")
	suite.writeReadCompare(c, filename, contents)
}

// TestWriteRead3 tests a simple write-read workflow with a small string.
func (suite *DriverSuite) TestWriteRead3(c *check.C) {
	filename := randomPath(32)
	contents := randomContents(32)
	suite.writeReadCompare(c, filename, contents)
}

// TestWriteRead4 tests a simple write-read workflow with 1MB of data.
func (suite *DriverSuite) TestWriteRead4(c *check.C) {
	filename := randomPath(32)
	contents := randomContents(1024 * 1024)
	suite.writeReadCompare(c, filename, contents)
}

// TestWriteReadNonUTF8 tests that non-utf8 data may be written to the storage
// driver safely.
func (suite *DriverSuite) TestWriteReadNonUTF8(c *check.C) {
	filename := randomPath(32)
	contents := []byte{0x80, 0x80, 0x80, 0x80}
	suite.writeReadCompare(c, filename, contents)
}

// TestTruncate tests that putting smaller contents than an original file does
// remove the excess contents.
func (suite *DriverSuite) TestTruncate(c *check.C) {
	filename := randomPath(32)
	contents := randomContents(1024 * 1024)
	suite.writeReadCompare(c, filename, contents)

	contents = randomContents(1024)
	suite.writeReadCompare(c, filename, contents)
}

// TestReadNonexistent tests reading content from an empty path.
func (suite *DriverSuite) TestReadNonexistent(c *check.C) {
	filename := randomPath(32)
	_, err := suite.StorageDriver.GetContent(filename)
	c.Assert(err, check.NotNil)
	c.Assert(err, check.FitsTypeOf, storagedriver.PathNotFoundError{})
}

// TestWriteReadStreams1 tests a simple write-read streaming workflow.
func (suite *DriverSuite) TestWriteReadStreams1(c *check.C) {
	filename := randomPath(32)
	contents := []byte("a")
	suite.writeReadCompareStreams(c, filename, contents)
}

// TestWriteReadStreams2 tests a simple write-read streaming workflow with
// unicode data.
func (suite *DriverSuite) TestWriteReadStreams2(c *check.C) {
	filename := randomPath(32)
	contents := []byte("\xc3\x9f")
	suite.writeReadCompareStreams(c, filename, contents)
}

// TestWriteReadStreams3 tests a simple write-read streaming workflow with a
// small amount of data.
func (suite *DriverSuite) TestWriteReadStreams3(c *check.C) {
	filename := randomPath(32)
	contents := randomContents(32)
	suite.writeReadCompareStreams(c, filename, contents)
}

// TestWriteReadStreams4 tests a simple write-read streaming workflow with 1MB
// of data.
func (suite *DriverSuite) TestWriteReadStreams4(c *check.C) {
	filename := randomPath(32)
	contents := randomContents(1024 * 1024)
	suite.writeReadCompareStreams(c, filename, contents)
}

// TestWriteReadStreamsNonUTF8 tests that non-utf8 data may be written to the
// storage driver safely.
func (suite *DriverSuite) TestWriteReadStreamsNonUTF8(c *check.C) {
	filename := randomPath(32)
	contents := []byte{0x80, 0x80, 0x80, 0x80}
	suite.writeReadCompareStreams(c, filename, contents)
}

// TestWriteReadLargeStreams tests that a 5GB file may be written to the storage
// driver safely.
func (suite *DriverSuite) TestWriteReadLargeStreams(c *check.C) {
	if testing.Short() {
		c.Skip("Skipping test in short mode")
	}

	filename := randomPath(32)
	defer suite.StorageDriver.Delete(firstPart(filename))

	checksum := sha1.New()
	var fileSize int64 = 5 * 1024 * 1024 * 1024

	contents := newRandReader(fileSize)
	written, err := suite.StorageDriver.WriteStream(filename, 0, io.TeeReader(contents, checksum))
	c.Assert(err, check.IsNil)
	c.Assert(written, check.Equals, fileSize)

	reader, err := suite.StorageDriver.ReadStream(filename, 0)
	c.Assert(err, check.IsNil)

	writtenChecksum := sha1.New()
	io.Copy(writtenChecksum, reader)

	c.Assert(writtenChecksum.Sum(nil), check.DeepEquals, checksum.Sum(nil))
}

// TestReadStreamWithOffset tests that the appropriate data is streamed when
// reading with a given offset.
func (suite *DriverSuite) TestReadStreamWithOffset(c *check.C) {
	filename := randomPath(32)
	defer suite.StorageDriver.Delete(firstPart(filename))

	chunkSize := int64(32)

	contentsChunk1 := randomContents(chunkSize)
	contentsChunk2 := randomContents(chunkSize)
	contentsChunk3 := randomContents(chunkSize)

	err := suite.StorageDriver.PutContent(filename, append(append(contentsChunk1, contentsChunk2...), contentsChunk3...))
	c.Assert(err, check.IsNil)

	reader, err := suite.StorageDriver.ReadStream(filename, 0)
	c.Assert(err, check.IsNil)
	defer reader.Close()

	readContents, err := ioutil.ReadAll(reader)
	c.Assert(err, check.IsNil)

	c.Assert(readContents, check.DeepEquals, append(append(contentsChunk1, contentsChunk2...), contentsChunk3...))

	reader, err = suite.StorageDriver.ReadStream(filename, chunkSize)
	c.Assert(err, check.IsNil)
	defer reader.Close()

	readContents, err = ioutil.ReadAll(reader)
	c.Assert(err, check.IsNil)

	c.Assert(readContents, check.DeepEquals, append(contentsChunk2, contentsChunk3...))

	reader, err = suite.StorageDriver.ReadStream(filename, chunkSize*2)
	c.Assert(err, check.IsNil)
	defer reader.Close()

	readContents, err = ioutil.ReadAll(reader)
	c.Assert(err, check.IsNil)
	c.Assert(readContents, check.DeepEquals, contentsChunk3)

	// Ensure we get invalid offest for negative offsets.
	reader, err = suite.StorageDriver.ReadStream(filename, -1)
	c.Assert(err, check.FitsTypeOf, storagedriver.InvalidOffsetError{})
	c.Assert(err.(storagedriver.InvalidOffsetError).Offset, check.Equals, int64(-1))
	c.Assert(err.(storagedriver.InvalidOffsetError).Path, check.Equals, filename)
	c.Assert(reader, check.IsNil)

	// Read past the end of the content and make sure we get a reader that
	// returns 0 bytes and io.EOF
	reader, err = suite.StorageDriver.ReadStream(filename, chunkSize*3)
	c.Assert(err, check.IsNil)
	defer reader.Close()

	buf := make([]byte, chunkSize)
	n, err := reader.Read(buf)
	c.Assert(err, check.Equals, io.EOF)
	c.Assert(n, check.Equals, 0)

	// Check the N-1 boundary condition, ensuring we get 1 byte then io.EOF.
	reader, err = suite.StorageDriver.ReadStream(filename, chunkSize*3-1)
	c.Assert(err, check.IsNil)
	defer reader.Close()

	n, err = reader.Read(buf)
	c.Assert(n, check.Equals, 1)

	// We don't care whether the io.EOF comes on the this read or the first
	// zero read, but the only error acceptable here is io.EOF.
	if err != nil {
		c.Assert(err, check.Equals, io.EOF)
	}

	// Any more reads should result in zero bytes and io.EOF
	n, err = reader.Read(buf)
	c.Assert(n, check.Equals, 0)
	c.Assert(err, check.Equals, io.EOF)
}

// TestContinueStreamAppendLarge tests that a stream write can be appended to without
// corrupting the data with a large chunk size.
func (suite *DriverSuite) TestContinueStreamAppendLarge(c *check.C) {
	suite.testContinueStreamAppend(c, int64(10*1024*1024))
}

// TestContinueStreamAppendSmall is the same as TestContinueStreamAppendLarge, but only
// with a tiny chunk size in order to test corner cases for some cloud storage drivers.
func (suite *DriverSuite) TestContinueStreamAppendSmall(c *check.C) {
	suite.testContinueStreamAppend(c, int64(32))
}

func (suite *DriverSuite) testContinueStreamAppend(c *check.C, chunkSize int64) {
	filename := randomPath(32)
	defer suite.StorageDriver.Delete(firstPart(filename))

	contentsChunk1 := randomContents(chunkSize)
	contentsChunk2 := randomContents(chunkSize)
	contentsChunk3 := randomContents(chunkSize)
	contentsChunk4 := randomContents(chunkSize)
	zeroChunk := make([]byte, int64(chunkSize))

	fullContents := append(append(contentsChunk1, contentsChunk2...), contentsChunk3...)

	nn, err := suite.StorageDriver.WriteStream(filename, 0, bytes.NewReader(contentsChunk1))
	c.Assert(err, check.IsNil)
	c.Assert(nn, check.Equals, int64(len(contentsChunk1)))

	fi, err := suite.StorageDriver.Stat(filename)
	c.Assert(err, check.IsNil)
	c.Assert(fi, check.NotNil)
	c.Assert(fi.Size(), check.Equals, int64(len(contentsChunk1)))

	nn, err = suite.StorageDriver.WriteStream(filename, fi.Size(), bytes.NewReader(contentsChunk2))
	c.Assert(err, check.IsNil)
	c.Assert(nn, check.Equals, int64(len(contentsChunk2)))

	fi, err = suite.StorageDriver.Stat(filename)
	c.Assert(err, check.IsNil)
	c.Assert(fi, check.NotNil)
	c.Assert(fi.Size(), check.Equals, 2*chunkSize)

	// Test re-writing the last chunk
	nn, err = suite.StorageDriver.WriteStream(filename, fi.Size()-chunkSize, bytes.NewReader(contentsChunk2))
	c.Assert(err, check.IsNil)
	c.Assert(nn, check.Equals, int64(len(contentsChunk2)))

	fi, err = suite.StorageDriver.Stat(filename)
	c.Assert(err, check.IsNil)
	c.Assert(fi, check.NotNil)
	c.Assert(fi.Size(), check.Equals, 2*chunkSize)

	nn, err = suite.StorageDriver.WriteStream(filename, fi.Size(), bytes.NewReader(fullContents[fi.Size():]))
	c.Assert(err, check.IsNil)
	c.Assert(nn, check.Equals, int64(len(fullContents[fi.Size():])))

	received, err := suite.StorageDriver.GetContent(filename)
	c.Assert(err, check.IsNil)
	c.Assert(received, check.DeepEquals, fullContents)

	// Writing past size of file extends file (no offest error). We would like
	// to write chunk 4 one chunk length past chunk 3. It should be successful
	// and the resulting file will be 5 chunks long, with a chunk of all
	// zeros.

	fullContents = append(fullContents, zeroChunk...)
	fullContents = append(fullContents, contentsChunk4...)

	nn, err = suite.StorageDriver.WriteStream(filename, int64(len(fullContents))-chunkSize, bytes.NewReader(contentsChunk4))
	c.Assert(err, check.IsNil)
	c.Assert(nn, check.Equals, chunkSize)

	fi, err = suite.StorageDriver.Stat(filename)
	c.Assert(err, check.IsNil)
	c.Assert(fi, check.NotNil)
	c.Assert(fi.Size(), check.Equals, int64(len(fullContents)))

	received, err = suite.StorageDriver.GetContent(filename)
	c.Assert(err, check.IsNil)
	c.Assert(len(received), check.Equals, len(fullContents))
	c.Assert(received[chunkSize*3:chunkSize*4], check.DeepEquals, zeroChunk)
	c.Assert(received[chunkSize*4:chunkSize*5], check.DeepEquals, contentsChunk4)
	c.Assert(received, check.DeepEquals, fullContents)

	// Ensure that negative offsets return correct error.
	nn, err = suite.StorageDriver.WriteStream(filename, -1, bytes.NewReader(zeroChunk))
	c.Assert(err, check.NotNil)
	c.Assert(err, check.FitsTypeOf, storagedriver.InvalidOffsetError{})
	c.Assert(err.(storagedriver.InvalidOffsetError).Path, check.Equals, filename)
	c.Assert(err.(storagedriver.InvalidOffsetError).Offset, check.Equals, int64(-1))
}

// TestReadNonexistentStream tests that reading a stream for a nonexistent path
// fails.
func (suite *DriverSuite) TestReadNonexistentStream(c *check.C) {
	filename := randomPath(32)

	_, err := suite.StorageDriver.ReadStream(filename, 0)
	c.Assert(err, check.NotNil)
	c.Assert(err, check.FitsTypeOf, storagedriver.PathNotFoundError{})

	_, err = suite.StorageDriver.ReadStream(filename, 64)
	c.Assert(err, check.NotNil)
	c.Assert(err, check.FitsTypeOf, storagedriver.PathNotFoundError{})
}

// TestList checks the returned list of keys after populating a directory tree.
func (suite *DriverSuite) TestList(c *check.C) {
	rootDirectory := "/" + randomFilename(int64(8+rand.Intn(8)))
	defer suite.StorageDriver.Delete(rootDirectory)

	parentDirectory := rootDirectory + "/" + randomFilename(int64(8+rand.Intn(8)))
	childFiles := make([]string, 50)
	for i := 0; i < len(childFiles); i++ {
		childFile := parentDirectory + "/" + randomFilename(int64(8+rand.Intn(8)))
		childFiles[i] = childFile
		err := suite.StorageDriver.PutContent(childFile, randomContents(32))
		c.Assert(err, check.IsNil)
	}
	sort.Strings(childFiles)

	keys, err := suite.StorageDriver.List("/")
	c.Assert(err, check.IsNil)
	c.Assert(keys, check.DeepEquals, []string{rootDirectory})

	keys, err = suite.StorageDriver.List(rootDirectory)
	c.Assert(err, check.IsNil)
	c.Assert(keys, check.DeepEquals, []string{parentDirectory})

	keys, err = suite.StorageDriver.List(parentDirectory)
	c.Assert(err, check.IsNil)

	sort.Strings(keys)
	c.Assert(keys, check.DeepEquals, childFiles)

	// A few checks to add here (check out #819 for more discussion on this):
	// 1. Ensure that all paths are absolute.
	// 2. Ensure that listings only include direct children.
	// 3. Ensure that we only respond to directory listings that end with a slash (maybe?).
}

// TestMove checks that a moved object no longer exists at the source path and
// does exist at the destination.
func (suite *DriverSuite) TestMove(c *check.C) {
	contents := randomContents(32)
	sourcePath := randomPath(32)
	destPath := randomPath(32)

	defer suite.StorageDriver.Delete(firstPart(sourcePath))
	defer suite.StorageDriver.Delete(firstPart(destPath))

	err := suite.StorageDriver.PutContent(sourcePath, contents)
	c.Assert(err, check.IsNil)

	err = suite.StorageDriver.Move(sourcePath, destPath)
	c.Assert(err, check.IsNil)

	received, err := suite.StorageDriver.GetContent(destPath)
	c.Assert(err, check.IsNil)
	c.Assert(received, check.DeepEquals, contents)

	_, err = suite.StorageDriver.GetContent(sourcePath)
	c.Assert(err, check.NotNil)
	c.Assert(err, check.FitsTypeOf, storagedriver.PathNotFoundError{})
}

// TestMoveOverwrite checks that a moved object no longer exists at the source
// path and overwrites the contents at the destination.
func (suite *DriverSuite) TestMoveOverwrite(c *check.C) {
	sourcePath := randomPath(32)
	destPath := randomPath(32)
	sourceContents := randomContents(32)
	destContents := randomContents(64)

	defer suite.StorageDriver.Delete(firstPart(sourcePath))
	defer suite.StorageDriver.Delete(firstPart(destPath))

	err := suite.StorageDriver.PutContent(sourcePath, sourceContents)
	c.Assert(err, check.IsNil)

	err = suite.StorageDriver.PutContent(destPath, destContents)
	c.Assert(err, check.IsNil)

	err = suite.StorageDriver.Move(sourcePath, destPath)
	c.Assert(err, check.IsNil)

	received, err := suite.StorageDriver.GetContent(destPath)
	c.Assert(err, check.IsNil)
	c.Assert(received, check.DeepEquals, sourceContents)

	_, err = suite.StorageDriver.GetContent(sourcePath)
	c.Assert(err, check.NotNil)
	c.Assert(err, check.FitsTypeOf, storagedriver.PathNotFoundError{})
}

// TestMoveNonexistent checks that moving a nonexistent key fails and does not
// delete the data at the destination path.
func (suite *DriverSuite) TestMoveNonexistent(c *check.C) {
	contents := randomContents(32)
	sourcePath := randomPath(32)
	destPath := randomPath(32)

	defer suite.StorageDriver.Delete(firstPart(destPath))

	err := suite.StorageDriver.PutContent(destPath, contents)
	c.Assert(err, check.IsNil)

	err = suite.StorageDriver.Move(sourcePath, destPath)
	c.Assert(err, check.NotNil)
	c.Assert(err, check.FitsTypeOf, storagedriver.PathNotFoundError{})

	received, err := suite.StorageDriver.GetContent(destPath)
	c.Assert(err, check.IsNil)
	c.Assert(received, check.DeepEquals, contents)
}

// TestDelete checks that the delete operation removes data from the storage
// driver
func (suite *DriverSuite) TestDelete(c *check.C) {
	filename := randomPath(32)
	contents := randomContents(32)

	defer suite.StorageDriver.Delete(firstPart(filename))

	err := suite.StorageDriver.PutContent(filename, contents)
	c.Assert(err, check.IsNil)

	err = suite.StorageDriver.Delete(filename)
	c.Assert(err, check.IsNil)

	_, err = suite.StorageDriver.GetContent(filename)
	c.Assert(err, check.NotNil)
	c.Assert(err, check.FitsTypeOf, storagedriver.PathNotFoundError{})
}

// TestURLFor checks that the URLFor method functions properly, but only if it
// is implemented
func (suite *DriverSuite) TestURLFor(c *check.C) {
	filename := randomPath(32)
	contents := randomContents(32)

	defer suite.StorageDriver.Delete(firstPart(filename))

	err := suite.StorageDriver.PutContent(filename, contents)
	c.Assert(err, check.IsNil)

	url, err := suite.StorageDriver.URLFor(filename, nil)
	if err == storagedriver.ErrUnsupportedMethod {
		return
	}
	c.Assert(err, check.IsNil)

	response, err := http.Get(url)
	c.Assert(err, check.IsNil)
	defer response.Body.Close()

	read, err := ioutil.ReadAll(response.Body)
	c.Assert(err, check.IsNil)
	c.Assert(read, check.DeepEquals, contents)

	url, err = suite.StorageDriver.URLFor(filename, map[string]interface{}{"method": "HEAD"})
	if err == storagedriver.ErrUnsupportedMethod {
		return
	}
	c.Assert(err, check.IsNil)

	response, err = http.Head(url)
	c.Assert(response.StatusCode, check.Equals, 200)
	c.Assert(response.ContentLength, check.Equals, int64(32))
}

// TestDeleteNonexistent checks that removing a nonexistent key fails.
func (suite *DriverSuite) TestDeleteNonexistent(c *check.C) {
	filename := randomPath(32)
	err := suite.StorageDriver.Delete(filename)
	c.Assert(err, check.NotNil)
	c.Assert(err, check.FitsTypeOf, storagedriver.PathNotFoundError{})
}

// TestDeleteFolder checks that deleting a folder removes all child elements.
func (suite *DriverSuite) TestDeleteFolder(c *check.C) {
	dirname := randomPath(32)
	filename1 := randomPath(32)
	filename2 := randomPath(32)
	filename3 := randomPath(32)
	contents := randomContents(32)

	defer suite.StorageDriver.Delete(firstPart(dirname))

	err := suite.StorageDriver.PutContent(path.Join(dirname, filename1), contents)
	c.Assert(err, check.IsNil)

	err = suite.StorageDriver.PutContent(path.Join(dirname, filename2), contents)
	c.Assert(err, check.IsNil)

	err = suite.StorageDriver.PutContent(path.Join(dirname, filename3), contents)
	c.Assert(err, check.IsNil)

	err = suite.StorageDriver.Delete(path.Join(dirname, filename1))
	c.Assert(err, check.IsNil)

	_, err = suite.StorageDriver.GetContent(path.Join(dirname, filename1))
	c.Assert(err, check.NotNil)
	c.Assert(err, check.FitsTypeOf, storagedriver.PathNotFoundError{})

	_, err = suite.StorageDriver.GetContent(path.Join(dirname, filename2))
	c.Assert(err, check.IsNil)

	_, err = suite.StorageDriver.GetContent(path.Join(dirname, filename3))
	c.Assert(err, check.IsNil)

	err = suite.StorageDriver.Delete(dirname)
	c.Assert(err, check.IsNil)

	_, err = suite.StorageDriver.GetContent(path.Join(dirname, filename1))
	c.Assert(err, check.NotNil)
	c.Assert(err, check.FitsTypeOf, storagedriver.PathNotFoundError{})

	_, err = suite.StorageDriver.GetContent(path.Join(dirname, filename2))
	c.Assert(err, check.NotNil)
	c.Assert(err, check.FitsTypeOf, storagedriver.PathNotFoundError{})

	_, err = suite.StorageDriver.GetContent(path.Join(dirname, filename3))
	c.Assert(err, check.NotNil)
	c.Assert(err, check.FitsTypeOf, storagedriver.PathNotFoundError{})
}

// TestStatCall runs verifies the implementation of the storagedriver's Stat call.
func (suite *DriverSuite) TestStatCall(c *check.C) {
	content := randomContents(4096)
	dirPath := randomPath(32)
	fileName := randomFilename(32)
	filePath := path.Join(dirPath, fileName)

	defer suite.StorageDriver.Delete(firstPart(dirPath))

	// Call on non-existent file/dir, check error.
	fi, err := suite.StorageDriver.Stat(dirPath)
	c.Assert(err, check.NotNil)
	c.Assert(err, check.FitsTypeOf, storagedriver.PathNotFoundError{})
	c.Assert(fi, check.IsNil)

	fi, err = suite.StorageDriver.Stat(filePath)
	c.Assert(err, check.NotNil)
	c.Assert(err, check.FitsTypeOf, storagedriver.PathNotFoundError{})
	c.Assert(fi, check.IsNil)

	err = suite.StorageDriver.PutContent(filePath, content)
	c.Assert(err, check.IsNil)

	// Call on regular file, check results
	fi, err = suite.StorageDriver.Stat(filePath)
	c.Assert(err, check.IsNil)
	c.Assert(fi, check.NotNil)
	c.Assert(fi.Path(), check.Equals, filePath)
	c.Assert(fi.Size(), check.Equals, int64(len(content)))
	c.Assert(fi.IsDir(), check.Equals, false)
	createdTime := fi.ModTime()

	// Sleep and modify the file
	time.Sleep(time.Second * 10)
	content = randomContents(4096)
	err = suite.StorageDriver.PutContent(filePath, content)
	c.Assert(err, check.IsNil)
	fi, err = suite.StorageDriver.Stat(filePath)
	c.Assert(err, check.IsNil)
	c.Assert(fi, check.NotNil)
	time.Sleep(time.Second * 5) // allow changes to propagate (eventual consistency)

	// Check if the modification time is after the creation time.
	// In case of cloud storage services, storage frontend nodes might have
	// time drift between them, however that should be solved with sleeping
	// before update.
	modTime := fi.ModTime()
	if !modTime.After(createdTime) {
		c.Errorf("modtime (%s) is before the creation time (%s)", modTime, createdTime)
	}

	// Call on directory (do not check ModTime as dirs don't need to support it)
	fi, err = suite.StorageDriver.Stat(dirPath)
	c.Assert(err, check.IsNil)
	c.Assert(fi, check.NotNil)
	c.Assert(fi.Path(), check.Equals, dirPath)
	c.Assert(fi.Size(), check.Equals, int64(0))
	c.Assert(fi.IsDir(), check.Equals, true)
}

// TestPutContentMultipleTimes checks that if storage driver can overwrite the content
// in the subsequent puts. Validates that PutContent does not have to work
// with an offset like WriteStream does and overwrites the file entirely
// rather than writing the data to the [0,len(data)) of the file.
func (suite *DriverSuite) TestPutContentMultipleTimes(c *check.C) {
	filename := randomPath(32)
	contents := randomContents(4096)

	defer suite.StorageDriver.Delete(firstPart(filename))
	err := suite.StorageDriver.PutContent(filename, contents)
	c.Assert(err, check.IsNil)

	contents = randomContents(2048) // upload a different, smaller file
	err = suite.StorageDriver.PutContent(filename, contents)
	c.Assert(err, check.IsNil)

	readContents, err := suite.StorageDriver.GetContent(filename)
	c.Assert(err, check.IsNil)
	c.Assert(readContents, check.DeepEquals, contents)
}

// TestConcurrentStreamReads checks that multiple clients can safely read from
// the same file simultaneously with various offsets.
func (suite *DriverSuite) TestConcurrentStreamReads(c *check.C) {
	var filesize int64 = 128 * 1024 * 1024

	if testing.Short() {
		filesize = 10 * 1024 * 1024
		c.Log("Reducing file size to 10MB for short mode")
	}

	filename := randomPath(32)
	contents := randomContents(filesize)

	defer suite.StorageDriver.Delete(firstPart(filename))

	err := suite.StorageDriver.PutContent(filename, contents)
	c.Assert(err, check.IsNil)

	var wg sync.WaitGroup

	readContents := func() {
		defer wg.Done()
		offset := rand.Int63n(int64(len(contents)))
		reader, err := suite.StorageDriver.ReadStream(filename, offset)
		c.Assert(err, check.IsNil)

		readContents, err := ioutil.ReadAll(reader)
		c.Assert(err, check.IsNil)
		c.Assert(readContents, check.DeepEquals, contents[offset:])
	}

	wg.Add(10)
	for i := 0; i < 10; i++ {
		go readContents()
	}
	wg.Wait()
}

// TestConcurrentFileStreams checks that multiple *os.File objects can be passed
// in to WriteStream concurrently without hanging.
func (suite *DriverSuite) TestConcurrentFileStreams(c *check.C) {
	// if _, isIPC := suite.StorageDriver.(*ipc.StorageDriverClient); isIPC {
	// 	c.Skip("Need to fix out-of-process concurrency")
	// }

	numStreams := 32

	if testing.Short() {
		numStreams = 8
		c.Log("Reducing number of streams to 8 for short mode")
	}

	var wg sync.WaitGroup

	testStream := func(size int64) {
		defer wg.Done()
		suite.testFileStreams(c, size)
	}

	wg.Add(numStreams)
	for i := numStreams; i > 0; i-- {
		go testStream(int64(numStreams) * 1024 * 1024)
	}

	wg.Wait()
}

// TestEventualConsistency checks that if stat says that a file is a certain size, then
// you can freely read from the file (this is the only guarantee that the driver needs to provide)
func (suite *DriverSuite) TestEventualConsistency(c *check.C) {
	if testing.Short() {
		c.Skip("Skipping test in short mode")
	}

	filename := randomPath(32)
	defer suite.StorageDriver.Delete(firstPart(filename))

	var offset int64
	var misswrites int
	var chunkSize int64 = 32

	for i := 0; i < 1024; i++ {
		contents := randomContents(chunkSize)
		read, err := suite.StorageDriver.WriteStream(filename, offset, bytes.NewReader(contents))
		c.Assert(err, check.IsNil)

		fi, err := suite.StorageDriver.Stat(filename)
		c.Assert(err, check.IsNil)

		// We are most concerned with being able to read data as soon as Stat declares
		// it is uploaded. This is the strongest guarantee that some drivers (that guarantee
		// at best eventual consistency) absolutely need to provide.
		if fi.Size() == offset+chunkSize {
			reader, err := suite.StorageDriver.ReadStream(filename, offset)
			c.Assert(err, check.IsNil)

			readContents, err := ioutil.ReadAll(reader)
			c.Assert(err, check.IsNil)

			c.Assert(readContents, check.DeepEquals, contents)

			reader.Close()
			offset += read
		} else {
			misswrites++
		}
	}

	if misswrites > 0 {
		c.Log("There were " + string(misswrites) + " occurences of a write not being instantly available.")
	}

	c.Assert(misswrites, check.Not(check.Equals), 1024)
}

// BenchmarkPutGetEmptyFiles benchmarks PutContent/GetContent for 0B files
func (suite *DriverSuite) BenchmarkPutGetEmptyFiles(c *check.C) {
	suite.benchmarkPutGetFiles(c, 0)
}

// BenchmarkPutGet1KBFiles benchmarks PutContent/GetContent for 1KB files
func (suite *DriverSuite) BenchmarkPutGet1KBFiles(c *check.C) {
	suite.benchmarkPutGetFiles(c, 1024)
}

// BenchmarkPutGet1MBFiles benchmarks PutContent/GetContent for 1MB files
func (suite *DriverSuite) BenchmarkPutGet1MBFiles(c *check.C) {
	suite.benchmarkPutGetFiles(c, 1024*1024)
}

// BenchmarkPutGet1GBFiles benchmarks PutContent/GetContent for 1GB files
func (suite *DriverSuite) BenchmarkPutGet1GBFiles(c *check.C) {
	suite.benchmarkPutGetFiles(c, 1024*1024*1024)
}

func (suite *DriverSuite) benchmarkPutGetFiles(c *check.C, size int64) {
	c.SetBytes(size)
	parentDir := randomPath(8)
	defer func() {
		c.StopTimer()
		suite.StorageDriver.Delete(firstPart(parentDir))
	}()

	for i := 0; i < c.N; i++ {
		filename := path.Join(parentDir, randomPath(32))
		err := suite.StorageDriver.PutContent(filename, randomContents(size))
		c.Assert(err, check.IsNil)

		_, err = suite.StorageDriver.GetContent(filename)
		c.Assert(err, check.IsNil)
	}
}

// BenchmarkStreamEmptyFiles benchmarks WriteStream/ReadStream for 0B files
func (suite *DriverSuite) BenchmarkStreamEmptyFiles(c *check.C) {
	suite.benchmarkStreamFiles(c, 0)
}

// BenchmarkStream1KBFiles benchmarks WriteStream/ReadStream for 1KB files
func (suite *DriverSuite) BenchmarkStream1KBFiles(c *check.C) {
	suite.benchmarkStreamFiles(c, 1024)
}

// BenchmarkStream1MBFiles benchmarks WriteStream/ReadStream for 1MB files
func (suite *DriverSuite) BenchmarkStream1MBFiles(c *check.C) {
	suite.benchmarkStreamFiles(c, 1024*1024)
}

// BenchmarkStream1GBFiles benchmarks WriteStream/ReadStream for 1GB files
func (suite *DriverSuite) BenchmarkStream1GBFiles(c *check.C) {
	suite.benchmarkStreamFiles(c, 1024*1024*1024)
}

func (suite *DriverSuite) benchmarkStreamFiles(c *check.C, size int64) {
	c.SetBytes(size)
	parentDir := randomPath(8)
	defer func() {
		c.StopTimer()
		suite.StorageDriver.Delete(firstPart(parentDir))
	}()

	for i := 0; i < c.N; i++ {
		filename := path.Join(parentDir, randomPath(32))
		written, err := suite.StorageDriver.WriteStream(filename, 0, bytes.NewReader(randomContents(size)))
		c.Assert(err, check.IsNil)
		c.Assert(written, check.Equals, size)

		rc, err := suite.StorageDriver.ReadStream(filename, 0)
		c.Assert(err, check.IsNil)
		rc.Close()
	}
}

// BenchmarkList5Files benchmarks List for 5 small files
func (suite *DriverSuite) BenchmarkList5Files(c *check.C) {
	suite.benchmarkListFiles(c, 5)
}

// BenchmarkList50Files benchmarks List for 50 small files
func (suite *DriverSuite) BenchmarkList50Files(c *check.C) {
	suite.benchmarkListFiles(c, 50)
}

func (suite *DriverSuite) benchmarkListFiles(c *check.C, numFiles int64) {
	parentDir := randomPath(8)
	defer func() {
		c.StopTimer()
		suite.StorageDriver.Delete(firstPart(parentDir))
	}()

	for i := int64(0); i < numFiles; i++ {
		err := suite.StorageDriver.PutContent(path.Join(parentDir, randomPath(32)), nil)
		c.Assert(err, check.IsNil)
	}

	c.ResetTimer()
	for i := 0; i < c.N; i++ {
		files, err := suite.StorageDriver.List(parentDir)
		c.Assert(err, check.IsNil)
		c.Assert(int64(len(files)), check.Equals, numFiles)
	}
}

// BenchmarkDelete5Files benchmarks Delete for 5 small files
func (suite *DriverSuite) BenchmarkDelete5Files(c *check.C) {
	suite.benchmarkDeleteFiles(c, 5)
}

// BenchmarkDelete50Files benchmarks Delete for 50 small files
func (suite *DriverSuite) BenchmarkDelete50Files(c *check.C) {
	suite.benchmarkDeleteFiles(c, 50)
}

func (suite *DriverSuite) benchmarkDeleteFiles(c *check.C, numFiles int64) {
	for i := 0; i < c.N; i++ {
		parentDir := randomPath(8)
		defer suite.StorageDriver.Delete(firstPart(parentDir))

		c.StopTimer()
		for j := int64(0); j < numFiles; j++ {
			err := suite.StorageDriver.PutContent(path.Join(parentDir, randomPath(32)), nil)
			c.Assert(err, check.IsNil)
		}
		c.StartTimer()

		// This is the operation we're benchmarking
		err := suite.StorageDriver.Delete(firstPart(parentDir))
		c.Assert(err, check.IsNil)
	}
}

func (suite *DriverSuite) testFileStreams(c *check.C, size int64) {
	tf, err := ioutil.TempFile("", "tf")
	c.Assert(err, check.IsNil)
	defer os.Remove(tf.Name())
	defer tf.Close()

	filename := randomPath(32)
	defer suite.StorageDriver.Delete(firstPart(filename))

	contents := randomContents(size)

	_, err = tf.Write(contents)
	c.Assert(err, check.IsNil)

	tf.Sync()
	tf.Seek(0, os.SEEK_SET)

	nn, err := suite.StorageDriver.WriteStream(filename, 0, tf)
	c.Assert(err, check.IsNil)
	c.Assert(nn, check.Equals, size)

	reader, err := suite.StorageDriver.ReadStream(filename, 0)
	c.Assert(err, check.IsNil)
	defer reader.Close()

	readContents, err := ioutil.ReadAll(reader)
	c.Assert(err, check.IsNil)

	c.Assert(readContents, check.DeepEquals, contents)
}

func (suite *DriverSuite) writeReadCompare(c *check.C, filename string, contents []byte) {
	defer suite.StorageDriver.Delete(firstPart(filename))

	err := suite.StorageDriver.PutContent(filename, contents)
	c.Assert(err, check.IsNil)

	readContents, err := suite.StorageDriver.GetContent(filename)
	c.Assert(err, check.IsNil)

	c.Assert(readContents, check.DeepEquals, contents)
}

func (suite *DriverSuite) writeReadCompareStreams(c *check.C, filename string, contents []byte) {
	defer suite.StorageDriver.Delete(firstPart(filename))

	nn, err := suite.StorageDriver.WriteStream(filename, 0, bytes.NewReader(contents))
	c.Assert(err, check.IsNil)
	c.Assert(nn, check.Equals, int64(len(contents)))

	reader, err := suite.StorageDriver.ReadStream(filename, 0)
	c.Assert(err, check.IsNil)
	defer reader.Close()

	readContents, err := ioutil.ReadAll(reader)
	c.Assert(err, check.IsNil)

	c.Assert(readContents, check.DeepEquals, contents)
}

var filenameChars = []byte("abcdefghijklmnopqrstuvwxyz0123456789")
var separatorChars = []byte("._-")

func randomPath(length int64) string {
	path := "/"
	for int64(len(path)) < length {
		chunkLength := rand.Int63n(length-int64(len(path))) + 1
		chunk := randomFilename(chunkLength)
		path += chunk
		remaining := length - int64(len(path))
		if remaining == 1 {
			path += randomFilename(1)
		} else if remaining > 1 {
			path += "/"
		}
	}
	return path
}

func randomFilename(length int64) string {
	b := make([]byte, length)
	wasSeparator := true
	for i := range b {
		if !wasSeparator && i < len(b)-1 && rand.Intn(4) == 0 {
			b[i] = separatorChars[rand.Intn(len(separatorChars))]
			wasSeparator = true
		} else {
			b[i] = filenameChars[rand.Intn(len(filenameChars))]
			wasSeparator = false
		}
	}
	return string(b)
}

func randomContents(length int64) []byte {
	b := make([]byte, length)
	for i := range b {
		b[i] = byte(rand.Intn(2 << 8))
	}
	return b
}

type randReader struct {
	r int64
	m sync.Mutex
}

func (rr *randReader) Read(p []byte) (n int, err error) {
	rr.m.Lock()
	defer rr.m.Unlock()
	for i := 0; i < len(p) && rr.r > 0; i++ {
		p[i] = byte(rand.Intn(255))
		n++
		rr.r--
	}
	if rr.r == 0 {
		err = io.EOF
	}
	return
}

func newRandReader(n int64) *randReader {
	return &randReader{r: n}
}

func firstPart(filePath string) string {
	if filePath == "" {
		return "/"
	}
	for {
		if filePath[len(filePath)-1] == '/' {
			filePath = filePath[:len(filePath)-1]
		}

		dir, file := path.Split(filePath)
		if dir == "" && file == "" {
			return "/"
		}
		if dir == "/" || dir == "" {
			return "/" + file
		}
		if file == "" {
			return dir
		}
		filePath = dir
	}
}
