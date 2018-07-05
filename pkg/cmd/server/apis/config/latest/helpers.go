package latest

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"io/ioutil"
	"path"
	"reflect"

	"github.com/ghodss/yaml"
	"github.com/golang/glog"

	"k8s.io/apimachinery/pkg/runtime"
	kyaml "k8s.io/apimachinery/pkg/util/yaml"

	configapi "github.com/openshift/origin/pkg/cmd/server/apis/config"
)

func ReadSessionSecrets(filename string) (*configapi.SessionSecrets, error) {
	config := &configapi.SessionSecrets{}
	if err := ReadYAMLFileInto(filename, config); err != nil {
		return nil, err
	}
	return config, nil
}

func ReadMasterConfig(filename string) (*configapi.MasterConfig, error) {
	config := &configapi.MasterConfig{}
	if err := ReadYAMLFileInto(filename, config); err != nil {
		return nil, err
	}
	return config, nil
}

func ReadAndResolveMasterConfig(filename string) (*configapi.MasterConfig, error) {
	masterConfig, err := ReadMasterConfig(filename)
	if err != nil {
		return nil, err
	}

	if err := configapi.ResolveMasterConfigPaths(masterConfig, path.Dir(filename)); err != nil {
		return nil, err
	}

	return masterConfig, nil
}

func ReadNodeConfig(filename string) (*configapi.NodeConfig, error) {
	config := &configapi.NodeConfig{}
	if err := ReadYAMLFileInto(filename, config); err != nil {
		return nil, err
	}
	return config, nil
}

func ReadAndResolveNodeConfig(filename string) (*configapi.NodeConfig, error) {
	nodeConfig, err := ReadNodeConfig(filename)
	if err != nil {
		return nil, err
	}

	if err := configapi.ResolveNodeConfigPaths(nodeConfig, path.Dir(filename)); err != nil {
		return nil, err
	}

	return nodeConfig, nil
}

// TODO: Remove this when a YAML serializer is available from upstream
func WriteYAML(obj runtime.Object) ([]byte, error) {
	json, err := runtime.Encode(Codec, obj)
	if err != nil {
		return nil, err
	}

	content, err := yaml.JSONToYAML(json)
	if err != nil {
		return nil, err
	}
	return content, err
}

func ReadYAML(reader io.Reader) (runtime.Object, error) {
	if reader == nil || reflect.ValueOf(reader).IsNil() {
		return nil, nil
	}
	data, err := ioutil.ReadAll(reader)
	if err != nil {
		return nil, err
	}
	jsonData, err := kyaml.ToJSON(data)
	if err != nil {
		return nil, err
	}
	obj, err := runtime.Decode(Codec, jsonData)
	if err != nil {
		return nil, captureSurroundingJSONForError("error reading config: ", jsonData, err)
	}
	// make sure there are no extra fields in jsonData
	if err := strictDecodeCheck(jsonData, obj); err != nil {
		return nil, err
	}
	return obj, nil
}

// TODO: Remove this when a YAML serializer is available from upstream
func ReadYAMLInto(data []byte, obj runtime.Object) error {
	jsonData, err := kyaml.ToJSON(data)
	if err != nil {
		return err
	}
	if err := runtime.DecodeInto(Codec, jsonData, obj); err != nil {
		return captureSurroundingJSONForError("error reading config: ", jsonData, err)
	}
	// make sure there are no extra fields in jsonData
	return strictDecodeCheck(jsonData, obj)
}

// strictDecodeCheck fails decodes when jsonData contains fields not included in the external version of obj
func strictDecodeCheck(jsonData []byte, obj runtime.Object) error {
	out, err := getExternalZeroValue(obj) // we need the external version of obj as that has the correct JSON struct tags
	if err != nil {
		glog.Errorf("Encountered config error %v in object %T, raw JSON:\n%s", err, obj, string(jsonData)) // TODO just return the error and die
		// never error for now, we need to determine a safe way to make this check fatal
		return nil
	}
	d := json.NewDecoder(bytes.NewReader(jsonData))
	d.DisallowUnknownFields()
	// note that we only care about the error, out is discarded
	if err := d.Decode(out); err != nil {
		glog.Errorf("Encountered config error %v in object %T, raw JSON:\n%s", err, obj, string(jsonData)) // TODO just return the error and die
	}
	// never error for now, we need to determine a safe way to make this check fatal
	return nil
}

// getExternalZeroValue returns the zero value of the external version of obj
func getExternalZeroValue(obj runtime.Object) (runtime.Object, error) {
	gvks, _, err := configapi.Scheme.ObjectKinds(obj)
	if err != nil {
		return nil, err
	}
	if len(gvks) == 0 { // should never happen
		return nil, fmt.Errorf("no gvks found for %#v", obj)
	}
	gvk := Version.WithKind(gvks[0].Kind)
	return configapi.Scheme.New(gvk)
}

func ReadYAMLFileInto(filename string, obj runtime.Object) error {
	data, err := ioutil.ReadFile(filename)
	if err != nil {
		return err
	}
	err = ReadYAMLInto(data, obj)
	if err != nil {
		return fmt.Errorf("could not load config file %q due to an error: %v", filename, err)
	}
	return nil
}

// TODO: we ultimately want a better decoder for JSON that allows us exact line numbers and better
// surrounding text description. This should be removed / replaced when that happens.
func captureSurroundingJSONForError(prefix string, data []byte, err error) error {
	if syntaxErr, ok := err.(*json.SyntaxError); err != nil && ok {
		offset := syntaxErr.Offset
		begin := offset - 20
		if begin < 0 {
			begin = 0
		}
		end := offset + 20
		if end > int64(len(data)) {
			end = int64(len(data))
		}
		return fmt.Errorf("%s%v (found near '%s')", prefix, err, string(data[begin:end]))
	}
	if err != nil {
		return fmt.Errorf("%s%v", prefix, err)
	}
	return err
}

// IsAdmissionPluginActivated returns true if the admission plugin is activated using configapi.DefaultAdmissionConfig
// otherwise it returns a default value
func IsAdmissionPluginActivated(reader io.Reader, defaultValue bool) (bool, error) {
	obj, err := ReadYAML(reader)
	if err != nil {
		return false, err
	}
	if obj == nil {
		return defaultValue, nil
	}
	activationConfig, ok := obj.(*configapi.DefaultAdmissionConfig)
	if !ok {
		// if we failed the cast, then we've got a config object specified for this admission plugin
		// that means that this must be enabled and all additional validation is up to the
		// admission plugin itself
		return true, nil
	}

	return !activationConfig.Disable, nil
}
