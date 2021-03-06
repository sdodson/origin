package api

import (
	"github.com/GoogleCloudPlatform/kubernetes/pkg/api"
)

func init() {
	api.Scheme.AddKnownTypes("",
		&Image{},
		&ImageList{},
		&ImageRepository{},
		&ImageRepositoryList{},
		&ImageRepositoryMapping{},
		&ImageRepositoryTag{},
		&ImageStreamImage{},
		&DockerImage{},
	)
}

func (*Image) IsAnAPIObject()                  {}
func (*ImageList) IsAnAPIObject()              {}
func (*ImageRepository) IsAnAPIObject()        {}
func (*ImageRepositoryList) IsAnAPIObject()    {}
func (*ImageRepositoryMapping) IsAnAPIObject() {}
func (*DockerImage) IsAnAPIObject()            {}
