#debuginfo not supported with Go
%global debug_package %{nil}
# modifying the Go binaries breaks the DWARF debugging
%global __os_install_post %{_rpmconfigdir}/brp-compress

%global gopath      %{_datadir}/gocode
%global import_path github.com/openshift/origin
%global sdn_import_path github.com/openshift/openshift-sdn
# The following should only be used for cleanup of sdn-ovs upgrades
%global kube_plugin_path /usr/libexec/kubernetes/kubelet-plugins/net/exec/redhat~openshift-ovs-subnet

# docker_version is the version of docker requires by packages
%global docker_version 1.9.1
# tuned_version is the version of tuned requires by packages
%global tuned_version  2.3
# openvswitch_version is the version of openvswitch requires by packages
%global openvswitch_version 2.3.1
# this is the version we obsolete up to. The packaging changed for Origin
# 1.0.6 and OSE 3.1 such that 'openshift' package names were no longer used.
%global package_refector_version 3.0.2.900
# %commit and %ldflags are intended to be set by tito custom builders provided
# in the .tito/lib directory. The values in this spec file will not be kept up to date.
%{!?commit:
%global commit 396b9105b2a5a41a04ca23c92a10d1ca9e21fa3c
}
%global shortcommit %(c=%{commit}; echo ${c:0:7})
# ldflags from hack/common.sh os::build:ldflags
%{!?ldflags:
%global ldflags -X github.com/openshift/origin/pkg/version.majorFromGit 1 -X github.com/openshift/origin/pkg/version.minorFromGit 2+ -X github.com/openshift/origin/pkg/version.versionFromGit v1.2.0-rc1 -X github.com/openshift/origin/pkg/version.commitFromGit 061e6d4 -X k8s.io/kubernetes/pkg/version.gitCommit 061e6d4 -X k8s.io/kubernetes/pkg/version.gitVersion v1.2.0-36-g4a3f9c5
}

%if 0%{?fedora} || 0%{?epel}
%global make_redistributable 0
%else
%global make_redistributable 1
%endif

%if "%{dist}" == ".el7aos"
%global package_name atomic-openshift
%global product_name Atomic OpenShift
%else
%global package_name origin
%global product_name Origin
%endif

Name:           %{package_name}
# Version is not kept up to date and is intended to be set by tito custom
# builders provided in the .tito/lib directory of this project
Version:        1.2.0
Release:        0.rc1%{?dist}
Summary:        Open Source Container Management by Red Hat
License:        ASL 2.0
URL:            https://%{import_path}
ExclusiveArch:  x86_64
Source0:        https://%{import_path}/archive/%{commit}/%{name}-%{version}.tar.gz
BuildRequires:  systemd
BuildRequires:  golang >= 1.4
Requires:       %{name}-clients = %{version}-%{release}
Requires:       iptables
Obsoletes:      openshift < %{package_refector_version}

#
# The following Bundled Provides entries are populated automatically by the
# OpenShift Origin tito custom builder found here:
#   https://github.com/openshift/origin/blob/master/.tito/lib/origin/builder/
#
# These are defined as per:
# https://fedoraproject.org/wiki/Packaging:Guidelines#Bundling_and_Duplication_of_system_libraries
#
### AUTO-BUNDLED-GEN-ENTRY-POINT

%description
Origin is a distribution of Kubernetes optimized for enterprise application
development and deployment, used by OpenShift 3 and Atomic Enterprise. Origin
adds developer and operational centric tools on top of Kubernetes to enable
rapid application development, easy deployment and scaling, and long-term
lifecycle maintenance for small and large teams and applications.

%package master
Summary:        %{product_name} Master
Requires:       %{name} = %{version}-%{release}
Requires(post):   systemd
Requires(preun):  systemd
Requires(postun): systemd
Obsoletes:      openshift-master < %{package_refector_version}

%description master
%{summary}

%package tests
Summary: %{product_name} Test Suite
Requires:       %{name} = %{version}-%{release}

%description tests
%{summary}

%package node
Summary:        %{product_name} Node
Requires:       %{name} = %{version}-%{release}
Requires:       docker >= %{docker_version}
Requires:       tuned-profiles-%{name}-node = %{version}-%{release}
Requires:       util-linux
Requires:       socat
Requires:       nfs-utils
Requires:       ethtool
Requires(post):   systemd
Requires(preun):  systemd
Requires(postun): systemd
Obsoletes:      openshift-node < %{package_refector_version}

%description node
%{summary}

%package -n tuned-profiles-%{name}-node
Summary:        Tuned profiles for %{product_name} Node hosts
Requires:       tuned >= %{tuned_version}
Obsoletes:      tuned-profiles-openshift-node < %{package_refector_version}

%description -n tuned-profiles-%{name}-node
%{summary}

%package clients
Summary:        %{product_name} Client binaries for Linux
Obsoletes:      openshift-clients < %{package_refector_version}
Requires:       git

%description clients
%{summary}

%if 0%{?make_redistributable}
%package clients-redistributable
Summary:        %{product_name} Client binaries for Linux, Mac OSX, and Windows
BuildRequires:  golang-pkg-darwin-amd64
BuildRequires:  golang-pkg-windows-386
Obsoletes:      openshift-clients-redistributable < %{package_refector_version}

%description clients-redistributable
%{summary}
%endif

%package dockerregistry
Summary:        Docker Registry v2 for %{product_name}
Requires:       %{name} = %{version}-%{release}

%description dockerregistry
%{summary}

%package pod
Summary:        %{product_name} Pod

%description pod
%{summary}

%package recycle
Summary:        %{product_name} Recycler
Requires:       %{name} = %{version}-%{release}

%description recycle
%{summary}

%package sdn-ovs
Summary:          %{product_name} SDN Plugin for Open vSwitch
Requires:         openvswitch >= %{openvswitch_version}
Requires:         %{name}-node = %{version}-%{release}
Requires:         bridge-utils
Requires:         ethtool
Requires:         procps-ng
Requires:         iproute
Obsoletes:        openshift-sdn-ovs < %{package_refector_version}

%description sdn-ovs
%{summary}

%prep
%setup -q

%build

# Don't judge me for this ... it's so bad.
mkdir _build

# Horrid hack because golang loves to just bundle everything
pushd _build
    mkdir -p src/github.com/openshift
    ln -s $(dirs +1 -l) src/%{import_path}
popd


# Gaming the GOPATH to include the third party bundled libs at build
# time.
mkdir _thirdpartyhacks
pushd _thirdpartyhacks
    ln -s \
        $(dirs +1 -l)/Godeps/_workspace/src/ \
            src
popd
export GOPATH=$(pwd)/_build:$(pwd)/_thirdpartyhacks:%{buildroot}%{gopath}:%{gopath}
# Build all linux components we care about
for cmd in oc openshift dockerregistry recycle
do
        go install -ldflags "%{ldflags}" %{import_path}/cmd/${cmd}
done
go test -c -o _build/bin/extended.test -ldflags "%{ldflags}" %{import_path}/test/extended

%if 0%{?make_redistributable}
# Build clients for other platforms
GOOS=windows GOARCH=386 go install -ldflags "%{ldflags}" %{import_path}/cmd/oc
GOOS=darwin GOARCH=amd64 go install -ldflags "%{ldflags}" %{import_path}/cmd/oc
%endif

#Build our pod
pushd images/pod/
    go build -ldflags "%{ldflags}" pod.go
popd

%install

install -d %{buildroot}%{_bindir}

# Install linux components
for bin in oc openshift dockerregistry recycle
do
  echo "+++ INSTALLING ${bin}"
  install -p -m 755 _build/bin/${bin} %{buildroot}%{_bindir}/${bin}
done
install -d %{buildroot}%{_libexecdir}/%{name}
install -p -m 755 _build/bin/extended.test %{buildroot}%{_libexecdir}/%{name}/

%if 0%{?make_redistributable}
# Install client executable for windows and mac
install -d %{buildroot}%{_datadir}/%{name}/{linux,macosx,windows}
install -p -m 755 _build/bin/oc %{buildroot}%{_datadir}/%{name}/linux/oc
install -p -m 755 _build/bin/darwin_amd64/oc %{buildroot}/%{_datadir}/%{name}/macosx/oc
install -p -m 755 _build/bin/windows_386/oc.exe %{buildroot}/%{_datadir}/%{name}/windows/oc.exe
%endif

#Install pod
install -p -m 755 images/pod/pod %{buildroot}%{_bindir}/

install -d -m 0755 %{buildroot}%{_unitdir}

mkdir -p %{buildroot}%{_sysconfdir}/sysconfig

for cmd in \
    atomic-enterprise \
    kube-apiserver \
    kube-controller-manager \
    kube-proxy \
    kube-scheduler \
    kubelet \
    kubernetes \
    oadm \
    openshift-deploy \
    openshift-docker-build \
    openshift-f5-router \
    openshift-router \
    openshift-sti-build \
    origin
do
    ln -s %{_bindir}/openshift %{buildroot}%{_bindir}/$cmd
done

ln -s oc %{buildroot}%{_bindir}/kubectl

install -d -m 0755 %{buildroot}%{_sysconfdir}/origin/{master,node}

# different service for origin vs aos
install -m 0644 contrib/systemd/%{name}-master.service %{buildroot}%{_unitdir}/%{name}-master.service
install -m 0644 contrib/systemd/%{name}-node.service %{buildroot}%{_unitdir}/%{name}-node.service
# same sysconfig files for origin vs aos
install -m 0644 contrib/systemd/origin-master.sysconfig %{buildroot}%{_sysconfdir}/sysconfig/%{name}-master
install -m 0644 contrib/systemd/origin-node.sysconfig %{buildroot}%{_sysconfdir}/sysconfig/%{name}-node
install -d -m 0755 %{buildroot}%{_prefix}/lib/tuned/%{name}-node-{guest,host}
install -m 0644 contrib/tuned/origin-node-guest/tuned.conf %{buildroot}%{_prefix}/lib/tuned/%{name}-node-guest/tuned.conf
install -m 0644 contrib/tuned/origin-node-host/tuned.conf %{buildroot}%{_prefix}/lib/tuned/%{name}-node-host/tuned.conf
install -d -m 0755 %{buildroot}%{_mandir}/man7

# Patch the manpage for tuned profiles on aos
%if "%{dist}" == ".el7aos"
%{__sed} -e 's|origin-node|atomic-openshift-node|g' \
 -e 's|ORIGIN_NODE|ATOMIC_OPENSHIFT_NODE|' \
 contrib/tuned/man/tuned-profiles-origin-node.7 > %{buildroot}%{_mandir}/man7/tuned-profiles-%{name}-node.7
%else
install -m 0644 contrib/tuned/man/tuned-profiles-origin-node.7 %{buildroot}%{_mandir}/man7/tuned-profiles-%{name}-node.7
%endif

mkdir -p %{buildroot}%{_sharedstatedir}/origin


# Install sdn scripts
install -d -m 0755 %{buildroot}%{_unitdir}/docker.service.d
install -p -m 0644 contrib/systemd/docker-sdn-ovs.conf %{buildroot}%{_unitdir}/docker.service.d/
pushd _thirdpartyhacks/src/%{sdn_import_path}/plugins/osdn/ovs/bin
   install -p -m 755 openshift-sdn-ovs %{buildroot}%{_bindir}/openshift-sdn-ovs
   install -p -m 755 openshift-sdn-docker-setup.sh %{buildroot}%{_bindir}/openshift-sdn-docker-setup.sh
popd
install -d -m 0755 %{buildroot}%{_unitdir}/%{name}-node.service.d
install -p -m 0644 contrib/systemd/openshift-sdn-ovs.conf %{buildroot}%{_unitdir}/%{name}-node.service.d/openshift-sdn-ovs.conf

# Install bash completions
install -d -m 755 %{buildroot}%{_sysconfdir}/bash_completion.d/
install -p -m 644 contrib/completions/bash/* %{buildroot}%{_sysconfdir}/bash_completion.d/
# Generate atomic-enterprise bash completions
%{__sed} -e "s|openshift|atomic-enterprise|g" contrib/completions/bash/openshift > %{buildroot}%{_sysconfdir}/bash_completion.d/atomic-enterprise

%files
%doc README.md
%license LICENSE
%{_bindir}/openshift
%{_bindir}/atomic-enterprise
%{_bindir}/kube-apiserver
%{_bindir}/kube-controller-manager
%{_bindir}/kube-proxy
%{_bindir}/kube-scheduler
%{_bindir}/kubelet
%{_bindir}/kubernetes
%{_bindir}/oadm
%{_bindir}/openshift-deploy
%{_bindir}/openshift-docker-build
%{_bindir}/openshift-f5-router
%{_bindir}/openshift-router
%{_bindir}/openshift-sti-build
%{_bindir}/origin
%{_sharedstatedir}/origin
%{_sysconfdir}/bash_completion.d/atomic-enterprise
%{_sysconfdir}/bash_completion.d/oadm
%{_sysconfdir}/bash_completion.d/openshift
%defattr(0700,-,-)
%dir %config(noreplace) %{_sysconfdir}/origin
%ghost %dir %config(noreplace) %{_sysconfdir}/origin
%ghost %config(noreplace) %{_sysconfdir}/origin/.config_managed

%pre
# If /etc/openshift exists and /etc/origin doesn't, symlink it to /etc/origin
if [ -d "%{_sysconfdir}/openshift" ]; then
  if ! [ -d "%{_sysconfdir}/origin"  ]; then
    ln -s %{_sysconfdir}/openshift %{_sysconfdir}/origin
  fi
fi
if [ -d "%{_sharedstatedir}/openshift" ]; then
  if ! [ -d "%{_sharedstatedir}/origin"  ]; then
    ln -s %{_sharedstatedir}/openshift %{_sharedstatedir}/origin
  fi
fi

%files tests
%{_libexecdir}/%{name}
%{_libexecdir}/%{name}/extended.test


%files master
%{_unitdir}/%{name}-master.service
%config(noreplace) %{_sysconfdir}/sysconfig/%{name}-master
%defattr(0700,-,-)
%config(noreplace) %{_sysconfdir}/origin/master
%ghost %config(noreplace) %{_sysconfdir}/origin/admin.crt
%ghost %config(noreplace) %{_sysconfdir}/origin/admin.key
%ghost %config(noreplace) %{_sysconfdir}/origin/admin.kubeconfig
%ghost %config(noreplace) %{_sysconfdir}/origin/ca.crt
%ghost %config(noreplace) %{_sysconfdir}/origin/ca.key
%ghost %config(noreplace) %{_sysconfdir}/origin/ca.serial.txt
%ghost %config(noreplace) %{_sysconfdir}/origin/etcd.server.crt
%ghost %config(noreplace) %{_sysconfdir}/origin/etcd.server.key
%ghost %config(noreplace) %{_sysconfdir}/origin/master-config.yaml
%ghost %config(noreplace) %{_sysconfdir}/origin/master.etcd-client.crt
%ghost %config(noreplace) %{_sysconfdir}/origin/master.etcd-client.key
%ghost %config(noreplace) %{_sysconfdir}/origin/master.kubelet-client.crt
%ghost %config(noreplace) %{_sysconfdir}/origin/master.kubelet-client.key
%ghost %config(noreplace) %{_sysconfdir}/origin/master.server.crt
%ghost %config(noreplace) %{_sysconfdir}/origin/master.server.key
%ghost %config(noreplace) %{_sysconfdir}/origin/openshift-master.crt
%ghost %config(noreplace) %{_sysconfdir}/origin/openshift-master.key
%ghost %config(noreplace) %{_sysconfdir}/origin/openshift-master.kubeconfig
%ghost %config(noreplace) %{_sysconfdir}/origin/openshift-registry.crt
%ghost %config(noreplace) %{_sysconfdir}/origin/openshift-registry.key
%ghost %config(noreplace) %{_sysconfdir}/origin/openshift-registry.kubeconfig
%ghost %config(noreplace) %{_sysconfdir}/origin/openshift-router.crt
%ghost %config(noreplace) %{_sysconfdir}/origin/openshift-router.key
%ghost %config(noreplace) %{_sysconfdir}/origin/openshift-router.kubeconfig
%ghost %config(noreplace) %{_sysconfdir}/origin/policy.json
%ghost %config(noreplace) %{_sysconfdir}/origin/serviceaccounts.private.key
%ghost %config(noreplace) %{_sysconfdir}/origin/serviceaccounts.public.key
%ghost %config(noreplace) %{_sysconfdir}/origin/.config_managed

%post master
%systemd_post %{name}-master.service
# Create master config and certs if both do not exist
if [[ ! -e %{_sysconfdir}/origin/master/master-config.yaml &&
     ! -e %{_sysconfdir}/origin/master/ca.crt ]]; then
  %{_bindir}/openshift start master --write-config=%{_sysconfdir}/origin/master
  # Create node configs if they do not already exist
  if ! find %{_sysconfdir}/origin/ -type f -name "node-config.yaml" | grep -E "node-config.yaml"; then
    %{_bindir}/oadm create-node-config --node-dir=%{_sysconfdir}/origin/node/ --node=localhost --hostnames=localhost,127.0.0.1 --node-client-certificate-authority=%{_sysconfdir}/origin/master/ca.crt --signer-cert=%{_sysconfdir}/origin/master/ca.crt --signer-key=%{_sysconfdir}/origin/master/ca.key --signer-serial=%{_sysconfdir}/origin/master/ca.serial.txt --certificate-authority=%{_sysconfdir}/origin/master/ca.crt
  fi
  # Generate a marker file that indicates config and certs were RPM generated
  echo "# Config generated by RPM at "`date -u` > %{_sysconfdir}/origin/.config_managed
fi


%preun master
%systemd_preun %{name}-master.service

%postun master
%systemd_postun

%files node
%{_unitdir}/%{name}-node.service
%config(noreplace) %{_sysconfdir}/sysconfig/%{name}-node
%defattr(0700,-,-)
%config(noreplace) %{_sysconfdir}/origin/node
%ghost %config(noreplace) %{_sysconfdir}/origin/node/node-config.yaml
%ghost %config(noreplace) %{_sysconfdir}/origin/.config_managed

%post node
%systemd_post %{name}-node.service

%preun node
%systemd_preun %{name}-node.service

%postun node
%systemd_postun

%files sdn-ovs
%dir %{_unitdir}/docker.service.d/
%dir %{_unitdir}/%{name}-node.service.d/
%{_bindir}/openshift-sdn-ovs
%{_bindir}/openshift-sdn-docker-setup.sh
%{_unitdir}/%{name}-node.service.d/openshift-sdn-ovs.conf
%{_unitdir}/docker.service.d/docker-sdn-ovs.conf

%posttrans sdn-ovs
# This path was installed by older packages but the directory wasn't owned by
# RPM so we need to clean it up otherwise kubelet throws an error trying to
# load the directory as a plugin
if [ -d %{kube_plugin_path} ]; then
  rmdir %{kube_plugin_path}
fi

%files -n tuned-profiles-%{name}-node
%license LICENSE
%{_prefix}/lib/tuned/%{name}-node-host
%{_prefix}/lib/tuned/%{name}-node-guest
%{_mandir}/man7/tuned-profiles-%{name}-node.7*

%post -n tuned-profiles-%{name}-node
recommended=`/usr/sbin/tuned-adm recommend`
if [[ "${recommended}" =~ guest ]] ; then
  /usr/sbin/tuned-adm profile %{name}-node-guest > /dev/null 2>&1
else
  /usr/sbin/tuned-adm profile %{name}-node-host > /dev/null 2>&1
fi

%preun -n tuned-profiles-%{name}-node
# reset the tuned profile to the recommended profile
# $1 = 0 when we're being removed > 0 during upgrades
if [ "$1" = 0 ]; then
  recommended=`/usr/sbin/tuned-adm recommend`
  /usr/sbin/tuned-adm profile $recommended > /dev/null 2>&1
fi

%files clients
%license LICENSE
%{_bindir}/oc
%{_bindir}/kubectl
%{_sysconfdir}/bash_completion.d/oc

%if 0%{?make_redistributable}
%files clients-redistributable
%dir %{_datadir}/%{name}/linux/
%dir %{_datadir}/%{name}/macosx/
%dir %{_datadir}/%{name}/windows/
%{_datadir}/%{name}/linux/oc
%{_datadir}/%{name}/macosx/oc
%{_datadir}/%{name}/windows/oc.exe
%endif

%files dockerregistry
%{_bindir}/dockerregistry

%files pod
%{_bindir}/pod

%files recycle
%{_bindir}/recycle


%changelog
* Thu Apr 21 2016 Scott Dodson <sdodson@redhat.com> 1.2.0
- All image references should be using full semantic version
  (ccoleman@redhat.com)
- debug for ext test failures on jenkins (gmontero@redhat.com)
- Revert "Retry import to the docker hub on 401" (ccoleman@redhat.com)
- debug for failures on jenkins (gmontero@redhat.com)
- force pull fixes / debug (gmontero@redhat.com)
- Change the context being used when Stat-ing remote registry
  (maszulik@redhat.com)
- Update 1 - run to the entire interval (ccoleman@redhat.com)
- Retry 401 unauthorized responses from registries within a window
  (ccoleman@redhat.com)
- Exclude deployment tests and set a perf test to serial (ccoleman@redhat.com)
- Add client debugging for legacy dockerregistry code (ccoleman@redhat.com)
- moved jUnit report for test-cmd to be consistent (skuznets@redhat.com)
- remove trailing = from set trigger example (bparees@redhat.com)
- haproxy obfuscated internal IP in routing cookie (pcameron@redhat.com)
- Example CLI command (ccoleman@redhat.com)
- Add summary status message to network test runner (marun@redhat.com)
- Revert "oc status must show monopods" (ccoleman@redhat.com)
- Refactor build strategy permissions into distinct roles (jliggitt@redhat.com)
- dind: Clean up check for ready nodes (marun@redhat.com)
- Cleanup network test runner's use of conditionals (marun@redhat.com)
- Copy config to dev cluster master's local storage (marun@redhat.com)
- Cleanup network test runner error handling (marun@redhat.com)
- Minimize image builds by the network test runner (marun@redhat.com)
- Improve network test runner error handling (marun@redhat.com)
- Reduce log verbosity of network test runner (marun@redhat.com)
- Remove redundant extended networking sanity tests (marun@redhat.com)
- Make /etc/origin /etc/origin/master /etc/origin/node 0700
  (sdodson@redhat.com)
- Fix precision of cpu to millicore and memory to bytes (decarr@redhat.com)
- UPSTREAM: 24208: Honor starting resourceVersion in watch cache
  (agoldste@redhat.com)
- [RPMS] Switch requires from docker-io to docker (sdodson@redhat.com)
- extended: Allow to focus on particular tests (miminar@redhat.com)
- Abuse deployments with extended test (ccoleman@redhat.com)
- UPSTREAM: 23435: Fixed mounting with containerized kubelet
  (jsafrane@redhat.com)
- dind: only wait for Ready non-sdn nodes (marun@redhat.com)
- Ensure stable route admission (marun@redhat.com)
- UPSTREAM: 23769: Ensure volume GetCloudProvider code uses cloud config
  (jliggitt@redhat.com)
- UPSTREAM: 21140: e2e test for dynamic provisioning. (jliggitt@redhat.com)
- UPSTREAM: 23463: add an event for when a daemonset can't place a pod due to
  insufficent resource or port conflict (jliggitt@redhat.com)
- UPSTREAM: 23929: only include running and pending pods in daemonset should
  place calculation (jliggitt@redhat.com)
- Update atomic registry quickstart artifacts (aweiteka@redhat.com)
- Update font-awesome bower dependency (spadgett@redhat.com)
- UPSTREAM: 23746: A pod never terminated if a container image registry was
  unavailable (agoldste@redhat.com)
- fix push path in log message (bparees@redhat.com)
- Bump fontawesome to 4.6.1 (jforrest@redhat.com)
- Fix unit tests (ironcladlou@gmail.com)
- Prevent concurrent deployer pod creation (ironcladlou@gmail.com)
- Enforce overview scaling rules for deployments without a service
  (spadgett@redhat.com)
- Added provisioning flag and refactored VolumeConfig struct names
  (mturansk@redhat.com)
- Fix bindata diff for new font-awesome release (spadgett@redhat.com)
- bump(github.com/openshift/openshift-sdn):
  9f1f60258fcef6f0ef647a75a8754bc80779c065 (rpenta@redhat.com)
- Fix e2e scc race (agoldste@redhat.com)
- UPSTREAM: 23894: Should not fail containers on OOM score adjust
  (ccoleman@redhat.com)
- Add ability to specify allowed CNs for RequestHeader proxy client cert
  (jliggitt@redhat.com)
- bump(k8s.io/kubernetes): 114a51dfbc43a8bcf07db1774a20e05d560e34b0
  (deads@redhat.com)
- Modify pullthrough import-image use case to use our cli framework
  (maszulik@redhat.com)
- add system:image-auditor (deads@redhat.com)
- deployer controller: ensure phase direction (mkargaki@redhat.com)
- Improve wording in sample-app README (rhcarvalho@gmail.com)
- Wrap login requests to clear in-memory session (jliggitt@redhat.com)
- Grant use of the NFS plugin in hostmount-anyuid SCC, to enable NFS recycler
  pods to run (pmorie@gmail.com)
- made hack/test-go handle compilation errors better (skuznets@redhat.com)
- Enable etcd cache for k8s resources (jliggitt@redhat.com)
- UPSTREAM: 24048: Use correct defaults when binding apiserver flags
  (jliggitt@redhat.com)
- UPSTREAM: 24008: Make watch cache behave like uncached watch
  (jliggitt@redhat.com)
- Getting docker logs always to debug issue 8399 (maszulik@redhat.com)
- deployment controller: cancel deployers on new cancelled deployments
  (mkargaki@redhat.com)
- Travis can't install go vet anymore (ccoleman@redhat.com)
- Add debugs for CPU Quota flake (mrunalp@gmail.com)
- UPSTREAM: 23793: Make ConfigMap volume readable as non-root
  (pmorie@gmail.com)
- Getting docker logs always to debug issue 8399 (maszulik@redhat.com)
- ProjectRequestLimit plugin: ignore projects in terminating state
  (cewong@redhat.com)
- Support focus arguments on both conformance and core (ccoleman@redhat.com)
- Bug 1324437: show cancel as subordinate to non-terminating phases
  (mkargaki@redhat.com)
- BZ_1324273: Make BC edit form dirty when deleting Key-Value pair
  (jhadvig@redhat.com)
- Add a conformance test for extended (ccoleman@redhat.com)
- Always set the Cmd for source Docker image (mfojtik@redhat.com)
- stylistic/refactoring changes for test/extended/cmd to use os::cmd
  (skuznets@redhat.com)
- UPSTREAM: 23445: Update port forward e2e for go 1.6 (agoldste@redhat.com)
- Naming inconsistancy fix (jhadvig@redhat.com)
- added jUnit XML publishing step to exit trap (skuznets@redhat.com)
- added support for os::cmd parsing to junitreport (skuznets@redhat.com)
- refactored nested suites builder (skuznets@redhat.com)
- configure test-cmd to emit parsable output for jUnit (skuznets@redhat.com)
- install iproute since the origin-base image dose not contain ip command
  (bmeng@redhat.com)
- Change RunOnce duration plugin to act as a limit instead of override
  (cewong@redhat.com)
- Make infra and shared resource namespaces immortal (jliggitt@redhat.com)
- UPSTREAM: 23883: Externalize immortal namespaces (jliggitt@redhat.com)
- add conformance tag to some extended build tests (bparees@redhat.com)
- add slow tag to jenkins plugin extended test (gmontero@redhat.com)
- Error on node startup using perFSGroup quota, but fs mounted with noquota.
  (dgoodwin@redhat.com)
- Bug 1323710: fix deploy --cancel message on subsequent calls
  (mkargaki@redhat.com)
- UPSTREAM: 23548: Check claimRef UID when processing a recycled PV, take 2
  (swagiaal@redhat.com)
- Updates to the 503 application unavailable page. (sgoodwin@redhat.com)
- Improve display of logs in web console (spadgett@redhat.com)
- bump(github.com/openshift/source-to-image):
  641b22d0a5e7a77f7dab2b1e75f563ba59a4ec96 (rhcarvalho@gmail.com)
- elevate privilegs when removing etcd binary store (skuznets@redhat.com)
- remove running containers in case of a sigterm (bparees@redhat.com)
- Add mounting volumes to privileged pods template (jcope@redhat.com)
- Show pulling / terminated status in pods donut (spadgett@redhat.com)
- Update the postCommit hook godoc to reflect API (ccoleman@redhat.com)
- oc describe build: improve output. (vsemushi@redhat.com)
- do not error on adding app label to objects if it exists (bparees@redhat.com)
- Add the openshift/origin-egress-router image (danw@redhat.com)
- remove credentials arg (aweiteka@redhat.com)
- remove atomic registry quickstart from images dir, also hack test script
  (aweiteka@redhat.com)
- Allow multiple routers to update route status (sross@redhat.com)
- change default volume size (gmontero@redhat.com)
- Bug 1322587 - NotFound error (404) when deleting layers is logged but we'll
  be continuing the execution. (maszulik@redhat.com)
- Separate out new-app code for reuse (ccoleman@redhat.com)
- Refactor new app and new build to use options struct (ccoleman@redhat.com)
- use restart sec to avoid default rate limit (pweil@redhat.com)
- Refactor start-build to use options style (ccoleman@redhat.com)
- Tolerate local Git repositories without an origin set (ccoleman@redhat.com)
- Add unique suffix to build post-hook containers (rhcarvalho@gmail.com)
- The router command should keep support for hostPort (ccoleman@redhat.com)
- UPSTREAM: 23586: don't sync deployment when pod selector is empty
  (jliggitt@redhat.com)
- UPSTREAM: 23586: validate that daemonsets don't have empty selectors on
  creation (jliggitt@redhat.com)
- no commit id in img name and add openshift org to image name for openshift-
  pipeline plugin extended test (gmontero@redhat.com)
- Set service account correctly in oadm registry, deprecate --credentials
  (jliggitt@redhat.com)
- Add tests for multiple IDPs (sgallagh@redhat.com)
- Encode provider name when redirecting to login page (jliggitt@redhat.com)
- Allow multiple web login methods (sgallagh@redhat.com)
- allow pvc by default (pweil@redhat.com)
- UPSTREAM: 23007: Kubectl shouldn't print throttling debug output
  (jliggitt@redhat.com)
- Resolve api groups in resolveresource (jliggitt@redhat.com)
- Improve provider selection page (jliggitt@redhat.com)
- fix a forgotten modification : 'sti->s2i' (qilin.wang@huawei.com)
- sort volumes for reconciliation (pweil@redhat.com)
- Fixed string formatting for glog.Infof in image prunning
  (maszulik@redhat.com)
- Set charset with content type (jliggitt@redhat.com)
- bump(github.com/openshift/source-to-image):
  48e62fd57bebba14e1d0f7a40a15b65dafa5458c (cewong@redhat.com)
- Fix 8162: project settings layout issues (admin@benjaminapetersen.me)
- UPSTREAM: 23456: don't sync daemonsets or controllers with selectors that
  match all pods (jliggitt@redhat.com)
- UPSTREAM: 23457: Do not track resource usage for host path volumes. They can
  contain loops. (jliggitt@redhat.com)
- UPSTREAM: 23325: Fix hairpin mode (jliggitt@redhat.com)
- UPSTREAM: 23019: Add a rate limiter to the GCE cloudprovider
  (jliggitt@redhat.com)
- UPSTREAM: 23141: kubelet: send all recevied pods in one update
  (jliggitt@redhat.com)
- UPSTREAM: 23143: Make kubelet default to 10ms for CPU quota if limit < 10m
  (jliggitt@redhat.com)
- UPSTREAM: 23034: Fix controller-manager race condition issue which cause
  endpoints flush during restart (jliggitt@redhat.com)
- bump inotify watches (jeder@redhat.com)
- Use scale subresource for DC scaling in web console (spadgett@redhat.com)
- Fixing typos (dmcphers@redhat.com)
- Disambiguate origin generators (jliggitt@redhat.com)
- Add explicit emptyDir volumes where possible (ironcladlou@gmail.com)
- Resource discovery integration test (jliggitt@redhat.com)
- UPSTREAM: <carry>: v1beta3: ensure only v1 appears in discovery for legacy
  API group (jliggitt@redhat.com)
- Use strategy proxy setting for script download (cewong@redhat.com)
- bump(github.com/openshift/source-to-image):
  2c0fc8ae6150b27396dc00907cac128eeda99b09 (cewong@redhat.com)
- Deployment tests should really be disabled in e2e (ccoleman@redhat.com)
- Retry when receiving an imagestreamtag not found error (ccoleman@redhat.com)
- fix useragent for SA (deads@redhat.com)
- Fix e2e test's check for determining that the router is up - wait for the
  healthz port to respond with success - HTTP status code 200. Still need to
  check for router pod to be born. (smitram@gmail.com)
- Bug 1318920: emit events for failed cancellations (mkargaki@redhat.com)
- tweak jenkins job to test unrelased versions of the plugin
  (gmontero@redhat.com)
- Fix oadm diagnostic (master-node check for ovs plugin) to retrieve the list
  of nodes running on the same machine as master. (avagarwa@redhat.com)
- E2e deployments filter is incorrect (ccoleman@redhat.com)
- scc volumes support (pweil@redhat.com)
- UPSTREAM: <carry>: scc volumes support (pweil@redhat.com)
- UPSTREAM: <carry>: v1beta3 scc volumes support (pweil@redhat.com)
- Reorder the debug pod name (ccoleman@redhat.com)
- use a first class field definition to identify scratch images
  (bparees@redhat.com)
- Remove project admin/edit ability to create daemonsets (jliggitt@redhat.com)
- Bug 1314270: force dc reconcilation on canceled deployments
  (mkargaki@redhat.com)
- controller: refactor deployer controller interfaces (mkargaki@redhat.com)
- cli: oc process should print errors to stderr (stefw@redhat.com)
- use emptydir for sample-app volumes (bparees@redhat.com)
- fix extended cmd.sh to handle faster importer (deads@redhat.com)
- #7976 : Initialize Binary source to an empty default state if type but no
  value set (for API v1) (roland@jolokia.org)
- Atomic registry quickstart image (aweiteka@redhat.com)
- Fix bug where router reload fails to run lsof - insufficient permissions with
  the hostnetwork scc. Reduce the lsof requirement since we now check for error
  codes [non zero means bind errors] and have a healthz check as a sanity
  check. Plus fixes as per @smarterclayton review comments. (smitram@gmail.com)
- Include branded header within <noscript> message. (sgoodwin@redhat.com)
- Better error message when JavaScript is disabled (jawnsy@redhat.com)
- Simplify synthetic skips so that no special chars are needed Isolate the
  package skipping into a single function. (jay@apache.org)
- add volume prereq to db template descriptions (bparees@redhat.com)
- UPSTREAM: 22525: Add e2e for remaining quota resources (decarr@redhat.com)
- Fix new-app template search with multiple matches (cewong@redhat.com)
- UPSTREAM: <carry>: Suppress aggressive output of warning
  (ccoleman@redhat.com)
- hardcode build name to expect instead of getting it from start-build output
  (bparees@redhat.com)
- New skips in extended tests (ccoleman@redhat.com)
- removed binary etcd store from test-cmd artfacts (skuznets@redhat.com)
- Fix resolver used for --image-stream param, annotation searcher output
  (cewong@redhat.com)
- UPSTREAM: 23065: Remove gce provider requirements from garbage collector test
  (tiwillia@redhat.com)
- Bindata change for error with quotes on project 404 (jforrest@redhat.com)
- Fixed error with quotes (jlam@snaplogic.com)
- Escape ANSI color codes in web console logs (spadgett@redhat.com)
- refactor to not use dot imports for heredoc (skuznets@redhat.com)
- Bug 1320335: Fix quoting for mysql probes (mfojtik@redhat.com)
- Add client utilities for iSCSI and Ceph. (jsafrane@redhat.com)
- loosen exec to allow SA checks for privileges (deads@redhat.com)
- Allow perFSGroup local quota in config on first node start.
  (dgoodwin@redhat.com)
- Ensure ingress host matches route host (marun@redhat.com)
- use a max value of 92233720368547 for cgroup values (bparees@redhat.com)
- Revert "temporarily disable cgroup limits on builds" (bparees@redhat.com)
- Enable extensions storage for batch/autoscaling (jliggitt@redhat.com)
- Add navbar-utility-mobile to error.html Fixes
  https://github.com/openshift/origin/issues/8198 (sgoodwin@redhat.com)
- Add /dev to node volumes (sdodson@redhat.com)
- Install e2fsprogs and xfsprogs into base image (sdodson@redhat.com)
- UPSTREAM: 23078: Check claimRef UID when processing a recycled PV
  (swagiaal@redhat.com)
- oc debug is not defaulting to TTY (ccoleman@redhat.com)
- UPSTREAM: revert: d54ed4e: 21373: kubelet: reading cloudinfo from cadvisor
  (deads@redhat.com)
- temporarily disable cgroup limits on builds (bparees@redhat.com)
- test/extended/images/mongodb_replica: add tests for mongodb replication
  (vsemushi@redhat.com)
- update generated code and docs (pweil@redhat.com)
- UPSTREAM: 22857: partial - ensure DetermineEffectiveSC retains the container
  setting for readonlyrootfs (pweil@redhat.com)
- UPSTREAM: <carry>: v1beta3 scc - read only root file system support
  (pweil@redhat.com)
- UPSTREAM: <carry>: scc - read only root file system support
  (pweil@redhat.com)
- UPSTREAM: 23279: kubectl: enhance podtemplate describer (mkargaki@redhat.com)
- oc: add volume info on the dc describer (mkargaki@redhat.com)
- Fix typo (tdawson@redhat.com)
- oc status must show monopods (ffranz@redhat.com)
- Verify yum installed rpms (tdawson@redhat.com)
- remove dead cancel code (bparees@redhat.com)
- Integration tests should use docker.ClientFromEnv() (ccoleman@redhat.com)
- Move upstream (ccoleman@redhat.com)
- hack/test-cmd.sh races against deployment controller (ccoleman@redhat.com)
- Enable the pod garbage collector (tiwillia@redhat.com)
- make who-can use resource arg format (deads@redhat.com)
- Bug in Kube API version group ordering (ccoleman@redhat.com)
- Fix precision displaying percentages in quota chart tooltip
  (spadgett@redhat.com)
- updated artifacts to contain docker log and exlucde etcd data dir
  (skuznets@redhat.com)
- Mount /var/log into node container (sdodson@redhat.com)
- Hide extra close buttons for task lists (spadgett@redhat.com)
- Test refactor (ccoleman@redhat.com)
- Disable failing upstream test (ccoleman@redhat.com)
- In the release target, only build linux/amd64 (ccoleman@redhat.com)
- Pod diagnostic check is not correct in go 1.6 (ccoleman@redhat.com)
- Update Dockerfile for origin-release to use Go 1.6 (ccoleman@redhat.com)
- Update build-go.sh to deal with Go 1.6 (ccoleman@redhat.com)
- Suppress Go 1.6 error on -X flag (ccoleman@redhat.com)
- Bug 1318537 - Add warning when trying to import non-existing tag
  (maszulik@redhat.com)
- Bug 1310062 - Fallback to http if status code is not 2xx/3xx when deleting
  layers. (maszulik@redhat.com)
- Log the reload output for admins in the router logs (ccoleman@redhat.com)
- Add RunOnceDuration and ProjectRequestLimit plugins to default plugin chains
  (cewong@redhat.com)
- Add kube component config tests, disable /logs on master, update kube-proxy
  init (jliggitt@redhat.com)
- Set terminal max-width to 100%% for mobile (spadgett@redhat.com)
- Hide the java link if the container is not ready (slewis@fusesource.com)
- Support limit quotas and scopes in UI (spadgett@redhat.com)
- Add test for patch+conflicts (jliggitt@redhat.com)
- Removed the stray line that unconditionally forced on the SYN eater.
  (bbennett@redhat.com)
- Remove large, unnecessary margin from bottom of create forms
  (spadgett@redhat.com)
- Use smaller log font size for mobile (spadgett@redhat.com)
- Adjust -webkit-scrollbar width and log-scroll-top affixed position. Fixes
  https://github.com/openshift/origin/issues/7963 (sgoodwin@redhat.com)
- UPSTREAM: 23145: Use versioned object when computing patch
  (jliggitt@redhat.com)
- Handle new volume source types on web console (ffranz@redhat.com)
- Show consistent pod status in web console as CLI (spadgett@redhat.com)
- PVCs should not be editable once bound (ffranz@redhat.com)
- bump(github.com/openshift/source-to-image):
  625b58aa422549df9338fdaced1b9444d2313a15 (rhcarvalho@gmail.com)
- bump(github.com/openshift/openshift-sdn):
  72d9ab84f4bf650d1922174e6a90bd06018003b4 (dcbw@redhat.com)
- Reworked image quota (miminar@redhat.com)
- Fix certificate display on mobile (spadgett@redhat.com)
- Don't show chromeless log link if log not available (spadgett@redhat.com)
- Include container ID in glog message (rhcarvalho@gmail.com)
- Ignore default security context constraints when running on kube
  (decarr@redhat.com)
- UPSTREAM: 21373: kubelet: reading cloudinfo from cadvisor (deads@redhat.com)
- fix typo in db template readme (bparees@redhat.com)
- oc: more status fixes (mkargaki@redhat.com)
- use transport defaults (deads@redhat.com)
- UPSTREAM: 23003: support CIDRs in NO_PROXY (deads@redhat.com)
- Don't autofocus catalog filter input (spadgett@redhat.com)
- Add e2fsprogs to base image (sdodson@redhat.com)
- pkg: cmd: cli: cmd: startbuild: close response body (runcom@redhat.com)
- UPSTREAM: 22852: Set a missing namespace on objects to admit
  (miminar@redhat.com)
- Bump kubernetes-container-terminal to 0.0.11 (spadgett@redhat.com)
- Handle fallback to docker.io for 1.9 docker, which uses docker.io in
  .docker/config.json (maszulik@redhat.com)
- oc: plumb error writer in oc edit (mkargaki@redhat.com)
- UPSTREAM: 22634: kubectl: print errors that wont be reloaded in the editor
  (mkargaki@redhat.com)
- Include all extended tests in a single binary (marun@redhat.com)
- Update swagger spec (jliggitt@redhat.com)
- bump(k8s.io/kubernetes): 4a3f9c5b19c7ff804cbc1bf37a15c044ca5d2353
  (jliggitt@redhat.com)
- bump(github.com/google/cadvisor): 546a3771589bdb356777c646c6eca24914fdd48b
  (jliggitt@redhat.com)
- add debug when extended build tests fail (bparees@redhat.com)
- clean up jenkins master/slave parameters (bparees@redhat.com)
- Web console: fix problem balancing create flow columns (spadgett@redhat.com)
- Tooltip for multiple ImageSources in BC editor (jhadvig@redhat.com)
- fix two broken extended tests (bparees@redhat.com)
- Bug fix so that table-mobile will word-wrap: break-word (rhamilto@redhat.com)
- Add preliminary quota support for emptyDir volumes on XFS.
  (dgoodwin@redhat.com)
- Bump unit test timeout (jliggitt@redhat.com)
- updated tmpdir for e2e-docker (skuznets@redhat.com)
- Load environment files in containerized systemd units (sdodson@redhat.com)
- Interesting changes for rebase (jliggitt@redhat.com)
- Extended test namespace creation fixes (jliggitt@redhat.com)
- Mechanical changes for rebase (jliggitt@redhat.com)
- fix credential lookup for authenticated image stream import
  (jliggitt@redhat.com)
- Generated docs, conversions, copies, completions (jliggitt@redhat.com)
- UPSTREAM: <carry>: Allow overriding default generators for run
  (jliggitt@redhat.com)
- UPSTREAM: 22921: Fix job selector validation and tests (jliggitt@redhat.com)
- UPSTREAM: 22919: Allow starting test etcd with http (jliggitt@redhat.com)
- Stack definition lists only at narrower widths (spadgett@redhat.com)
- Disable externalIP by default (ccoleman@redhat.com)
- oc: warn about missing stream when deleting a tag (mkargaki@redhat.com)
- Revert "platformmanagement_public_425 - add quota information to oc describe
  is" (miminar@redhat.com)
- implemented miscellaneous iprovements for test-cmd (skuznets@redhat.com)
- Handle env vars that use valueFrom (jhadvig@redhat.com)
- UPSTREAM: 22917: Decrease verbosity of namespace controller trace logging
  (jliggitt@redhat.com)
- UPSTREAM: 22916: Correctly identify namespace subresources in GetRequestInfo
  (jliggitt@redhat.com)
- UPSTREAM: 22914: Move TestRuntimeCache into runtime_cache.go file
  (jliggitt@redhat.com)
- UPSTREAM: 22913: register internal types with scheme for reference unit test
  (jliggitt@redhat.com)
- UPSTREAM: 22910: Decrease parallelism in deletecollection test, lengthen test
  etcd certs (jliggitt@redhat.com)
- UPSTREAM: 22875: Tolerate multiple registered versions in a single group
  (jliggitt@redhat.com)
- UPSTREAM: 22877: mark filename flags for completions (ffranz@redhat.com)
- UPSTREAM: 22929: Test relative timestamps using UTC (jliggitt@redhat.com)
- UPSTREAM: 22746: add user-agent defaulting for discovery (deads@redhat.com)
- bump(github.com/Sirupsen/logrus): aaf92c95712104318fc35409745f1533aa5ff327
  (jliggitt@redhat.com)
- bump(github.com/hashicorp/golang-lru):
  a0d98a5f288019575c6d1f4bb1573fef2d1fcdc4 (jliggitt@redhat.com)
- bump(bitbucket.org/ww/goautoneg): 75cd24fc2f2c2a2088577d12123ddee5f54e0675
  (jliggitt@redhat.com)
- bump(k8s.io/kubernetes): 148dd34ab0e7daeb82582d6ea8e840c15a24e745
  (jliggitt@redhat.com)
- Update copy-kube-artifacts script (jliggitt@redhat.com)
- Allow recursive unit testing packages under godeps (jliggitt@redhat.com)
- Update godepchecker to print commit dates, allow checking out commits
  (jliggitt@redhat.com)
- Ensure errors are reported back in the container logs. (smitram@gmail.com)
- UPSTREAM: 22999: Display a better login message (ccoleman@redhat.com)
- move-upstream should use UPSTREAM_REPO_LOCATION like cherry-pick
  (ccoleman@redhat.com)
- oc: better new-app suggestions (mkargaki@redhat.com)
- Update javaLink extension (admin@benjaminapetersen.me)
- add parameter to start OS server with latest images (skuznets@redhat.com)
- parameterize IS namespace (gmontero@redhat.com)
- added test to decode and validate ldap sync config fixtures
  (skuznets@redhat.com)
- Bug 1317783: avoid shadowing errors in the deployment controller
  (mkargaki@redhat.com)
- Add a test of services/service isolation to tests/e2e/networking/
  (danw@redhat.com)
- Run the isolation extended networking tests under both plugins
  (danw@redhat.com)
- Make sanity and isolation network tests pass in a single-node environment
  (danw@redhat.com)
- Update extended networking tests to use k8s e2e utilities (danw@redhat.com)
- UPSTREAM: 22303: Make net e2e helpers public for 3rd party reuse
  (danw@gnome.org)
- Handle parametrized content types for build triggers (jimmidyson@gmail.com)
- Fix for bugz https://bugzilla.redhat.com/show_bug.cgi?id=1316698 and issue
  #7444   o Fixes as per @pweil- and @marun review comments.   o Fixes as per
  @smarterclayton review comments. (smitram@gmail.com)
- Ensure we are clean to docker.io/* images during hack/release.sh
  (ccoleman@redhat.com)
- make userAgentMatching take a set of required and deny regexes
  (deads@redhat.com)
- UPSTREAM: 22746: add user-agent defaulting for discovery (deads@redhat.com)
- fine tune which template parameter error types are returned
  (gmontero@redhat.com)
- Add ConfigMap permissions (pmorie@gmail.com)
- place tmp secret files in tmpdir (skuznets@redhat.com)
- Slim down issue template appearance (jliggitt@redhat.com)
- remove test file cruft (skuznets@redhat.com)
- Bug 1316749: prompt warning when scaling test deployments
  (mkargaki@redhat.com)
- Remove description field from types (mfojtik@redhat.com)
- UPSTREAM: 22929: Test relative timestamps using UTC (jliggitt@redhat.com)
- DETECT_RACES doesn't work (ccoleman@redhat.com)
- Add policy constraints for node targeting (jolamb@redhat.com)
- Mark filename flags for completions (ffranz@redhat.com)
- UPSTREAM: 22877: mark filename flags for completions (ffranz@redhat.com)
- Send graceful shutdown signal to all haproxy processes + wait for process to
  start listening, fixes as per @smarterclayton review comments and for
  integration tests. (smitram@gmail.com)
- [RPMS] Add extended.test to /usr/libexec/origin/extended.test
  (sdodson@redhat.com)
- always flush glog before returning from build logic (bparees@redhat.com)
- Improving markup semantics and appearance of display of Volumes data
  (rhamilto@redhat.com)
- Bumping openshift-object-describer to v1.1.2 (rhamilto@redhat.com)
- Bump grunt-contrib-uglify to 0.6.0 (spadgett@redhat.com)
- Export OS_OUTPUT_GOPATH=1 in Makefile (stefw@redhat.com)
- Bug fix for long, unbroken words that don't wrap in pod template
  (rhamilto@redhat.com)
- Fix test with build reference cycle (rhcarvalho@gmail.com)
- updated issue template (skuznets@redhat.com)
- Rename misleading util function (rhcarvalho@gmail.com)
- Only check circular references for oc new-build (rhcarvalho@gmail.com)
- Extract TestBuildOutputCycleDetection (rhcarvalho@gmail.com)
- Fixes rsh usage (ffranz@redhat.com)
- made edge language less ambiguous (skuznets@redhat.com)
- Increase sdn node provisioning timeout (marun@redhat.com)
- Set default template router reload interval to 5 seconds. (smitram@gmail.com)
- Remove left over after move to test/integration (rhcarvalho@gmail.com)
- Improved next steps pages for bcs using sample repos (ffranz@redhat.com)
- Remove dead code (rhcarvalho@gmail.com)
- oc new-app/new-build: handle the case when an imagestream matches but has no
  tags (cewong@redhat.com)
- Add the ability to install iptables rules to eat SYN packets targeted to
  haproxy while the haproxy reload happens.  This prevents traffic to haproxy
  getting dropped if it connects while the reload is in progess.
  (bbennett@redhat.com)
- sample-app: update docs (mkargaki@redhat.com)
- bump(github.com/openshift/source-to-image):
  fb7794026064c5a7b83905674a5244916a07fef9 (rhcarvalho@gmail.com)
- Fixing BZ1291521 where long project name spills out of modal
  (rhamilto@redhat.com)
- Moving overflow:hidden to specifically target  long replication controller or
  deployment name instead of deployment-block when caused another issue.  -
  Fixes https://github.com/openshift/origin/issues/7887 (sgoodwin@redhat.com)
- changed find behavior for OSX compatibility (skuznets@redhat.com)
- add debug statements for test-go (skuznets@redhat.com)
- Improve log text highlighting in Firefox (spadgett@redhat.com)
- Fixes [options] in usage (ffranz@redhat.com)
- Prevent last catalog tile from stretching to 100%% width
  (spadgett@redhat.com)
- Fix default cert for edge route not being used - fixes #7904
  (smitram@gmail.com)
- Initial addition of issue template (mfojtik@redhat.com)
- Fix deployment page layout problems (spadgett@redhat.com)
- allow different cert serial number generators (deads@redhat.com)
- Enabling LessCSS source maps for development (rhamilto@redhat.com)
- Prevent fieldset from expanding due to content (jawnsy@redhat.com)
- Add placement and container to popover and tooltip into popover.js so that
  messages aren't hidden when spanning multiple scrollable areas.  - Fixes
  https://github.com/openshift/origin/issues/7723 (sgoodwin@redhat.com)
- bump(k8s.io/kubernetes): 91d3e753a4eca4e87462b7c9e5391ec94bb792d9
  (jliggitt@redhat.com)
- Add liveness and readiness probe for Jenkins (mfojtik@redhat.com)
- Fix word-break in Firefox (spadgett@redhat.com)
- oc: update route warnings for oc status (mkargaki@redhat.com)
- Allow extra trusted bundles when generating master certs, node config, or
  kubeconfig (jliggitt@redhat.com)
- Add table-bordered styles to service port table (spadgett@redhat.com)
- nocache should be noCache (haowang@redhat.com)
- Update README.md (ccoleman@redhat.com)
- Update README.md (ccoleman@redhat.com)
- Update README (ccoleman@redhat.com)
- Break words when wrapping values in environment table (spadgett@redhat.com)
- Improve deployment name wrapping on overview page (spadgett@redhat.com)
- Drop capabilities when running s2i build container (cewong@redhat.com)
- bump(github.com/openshift/source-to-image)
  0278ed91e641158fbbf1de08808a12d5719322d8 (cewong@redhat.com)
- Bug 1315595: Use in-container env vars for liveness/readiness probes
  (mfojtik@redhat.com)
- deploy: more informative cancellation event on dc (mkargaki@redhat.com)
- Fixing typo (jhadvig@redhat.com)
- Show kind in editor modal (spadgett@redhat.com)
- rsync must validate if pod exists (ffranz@redhat.com)
- Minor fixes to Jenkins kubernetes readme (mfojtik@redhat.com)
- Breadcrumbs unification (jhadvig@redhat.com)
- Move hack/test-cmd_util.sh to test-util.sh, messing with script-fu
  (ccoleman@redhat.com)
- test-cmd: mktemp --suffix is not supported in Mac (mkargaki@redhat.com)
- Fix hardcoded f5 username (admin). (smitram@gmail.com)
- Add "quickstart" to web console browse menu (spadgett@redhat.com)
- Add active deadline to browse pod page (spadgett@redhat.com)
- Unconfuse web console about resource and kind (spadgett@redhat.com)
- Fix role addition for kube e2e tests (marun@redhat.com)
- UPSTREAM: 22516: kubectl: set maxUnavailable to 1 if both fenceposts resolve
  to zero (mkargaki@redhat.com)
- Add pods donut to deployment page (spadgett@redhat.com)
- deploy: emit events on the dc instead of its rcs (mkargaki@redhat.com)
- prevent skewed client updates (deads@redhat.com)
- oc new-build: add --image-stream flag (cewong@redhat.com)
- UPSTREAM: 22526: kubectl: bring the rolling updater on par with the
  deployments (mkargaki@redhat.com)
- add oc status warnings for missing is/istag/dockref/isimg for bc
  (gmontero@redhat.com)
- Update skip tags for gluster and ceph. (jay@apache.org)
- Skip quota check when cluster roles are outdated (miminar@redhat.com)
- Put dev cluster unit files in /etc/systemd/system (marun@redhat.com)
- dind: skip building etcd (marun@redhat.com)
- dind: disable sdn node at the end of provisioning (marun@redhat.com)
- Simplify vagrant/dind host provisioning (marun@redhat.com)
- Remove / fix dead code (ccoleman@redhat.com)
- UPSTREAM: <carry>: fix casting errors in case of obj nil
  (jawed.khelil@amadeus.com)
- Show log output in conversion generation (ccoleman@redhat.com)
- Support in-cluster-config for registry (ccoleman@redhat.com)
- Upgrade the registry to create secrets and service accounts
  (ccoleman@redhat.com)
- Support overriding the hostname in the router (ccoleman@redhat.com)
- Remove invisible browse option from web console catalog (spadgett@redhat.com)
- Set source of incremental build artifacts (rhcarvalho@gmail.com)
- bump(github.com/openshift/source-to-image):
  2e889d092f8f3fd0266610fa6b4d92db999ef68f (rhcarvalho@gmail.com)
- Use conventional profiler setup code (dmace@redhat.com)
- fixes bug 1312218 (bugzilla), fixes #7646 (github)
  (admin@benjaminapetersen.me)
- add discovery cache (deads@redhat.com)
- Making margin consistent around alerts inside.modal-resource-edit
  (rhamilto@redhat.com)
- Support HTTP pprof server in registry (dmace@redhat.com)
- platformmanagement_public_425 - add quota information to oc describe is
  (maszulik@redhat.com)
- oc: hide markers from different projects on oc status (mkargaki@redhat.com)
- Removing .page-header from About as the visuals aren't "right" for the page
  (rhamilto@redhat.com)
- bump(github.com/openshift/openshift-sdn):
  58baf17e027bc1fd913cddd55c5eed4782400c60 (danw@redhat.com)
- UPSTREAM: revert: 902e416: <carry>: v1beta3 scc (dgoodwin@redhat.com)
- UPSTREAM: revert: 7d1b481: <carry>: scc (dgoodwin@redhat.com)
- Fixed races in ratelimiter tests on go1.5 (maszulik@redhat.com)
- Dashboard extended test should not be run (ccoleman@redhat.com)
- make all alias correctly (deads@redhat.com)
- Bug 1310616: Validate absolute dir in build secret for docker strategy in oc
  new-build (mfojtik@redhat.com)
- Remove unnecessary word from oc volume command (nakayamakenjiro@gmail.com)
- Resolving visual defect on Storage .page-header (rhamilto@redhat.com)
- Cleaning up random drop shadow and rounded corners on messenger messages
  (rhamilto@redhat.com)
- Revert "Updates to use the SCC allowEmptyDirVolumePlugin setting."
  (dgoodwin@redhat.com)
- UPSTREAM: <carry>: Increase test etcd request timeout to 30s
  (ccoleman@redhat.com)
- Correcting colspan value to resolve cosmetic bug with missing right border on
  <thead> (rhamilto@redhat.com)
- ignore unrelated build+pod events during tests (bparees@redhat.com)
- Fix services e2e tests for dev clusters (marun@redhat.com)
- tweak registry roles (deads@redhat.com)
- export OS_OUTPUT_GOPATH for target build (jawed.khelil@amadeus.com)
- Adjust kube-topology so that it doesn't extend off of iOS viewport. Move
  bottom spacing from container-fluid to tab-content. (sgoodwin@redhat.com)
- Make mktmp call in common.sh compatible with OS X (cewong@redhat.com)
- Update external examples to include readiness/liveness probes
  (mfojtik@redhat.com)
- Fix build link in alert message (spadgett@redhat.com)
- Make "other routes" link go to browse routes page (spadgett@redhat.com)
- Skip hostPath test for upstream conformance test. (jay@apache.org)
- oc rsync: do not set owner when extracting with the tar strategy
  (cewong@redhat.com)
- removed SAR logfile from artifacts (skuznets@redhat.com)
- integration: Retry import from external registries when not reachable
  (miminar@redhat.com)
- Prevent log line number selection in Chrome (spadgett@redhat.com)
- Add create route button padding on mobile (jhadvig@redhat.com)
- test-cmd: ensure oc apply works with lists (mkargaki@redhat.com)
- UPSTREAM: 20948: Fix reference to versioned object in kubectl apply
  (mkargaki@redhat.com)
- Fix intra-pod kube e2e test (marun@redhat.com)
- Web console: fix problems with display route and route warnings
  (spadgett@redhat.com)
- Added more cmd tests for import-image to cover main branches
  (maszulik@redhat.com)
- Support API group and version in SAR/RAR (jliggitt@redhat.com)
- WIP: Enable FSGroup in restricted and hostNS SCCs (pmorie@gmail.com)
- Restrict events filter to certain fields in web console (spadgett@redhat.com)
- Pick correct strategy for binary builds (cewong@redhat.com)
- Metrics: show missing data as gaps in the chart (spadgett@redhat.com)
- Issue 7555 - fixed importimage which was picking wrong docker pull spec for
  images that failed previous import. (maszulik@redhat.com)
- configchange: correlate triggers with the generated cause
  (mkargaki@redhat.com)
- Refactor import-image to Complete-Validate-Run scheme. Additionally split the
  code so it's testable + added tests. (maszulik@redhat.com)
- Adds completion for oc rsh command (akram@free.fr)
- Fix swagger description generation (jliggitt@redhat.com)
- Allow externalizing/encrypting config values (jliggitt@redhat.com)
- Add encrypt/decrypt helper commands (jliggitt@redhat.com)
- bump all template mem limits to 512 Mi (gmontero@redhat.com)
- Bug fix for negative reload intervals - bugz 1311459. (smitram@gmail.com)
- Fixes as per @smarterclayton's review comments. (smitram@gmail.com)
- Use http[s] ports for environment values. Allows router ports to be overriden
  + multiple instances to run with host networking. (smitram@gmail.com)
- Switch from margin to padding and move it to the container-fluid div so gray
  bg extends length of page and maintains bottom spacing across pages Include
  fix to prevent filter appended button from wrapping in Safari
  (sgoodwin@redhat.com)
- check covers for role changes (deads@redhat.com)
- favicon.ico not copied during asset build (jforrest@redhat.com)
- Added liveness and readiness probes to database templates
  (mfojtik@redhat.com)
- enabled junitreport tool to stream output (skuznets@redhat.com)
- BZ_1312819: Can not add Environment Variables on buildconfig edit page
  (jhadvig@redhat.com)
- rewrite hack/test-go.sh (skuznets@redhat.com)
- UPSTREAM: <drop>: patch for 16146: Fix validate event for non-namespaced
  kinds (deads@redhat.com)
- added commands to manage serviceaccounts (skuznets@redhat.com)
- configchange: proceed with deployment with non-automatic ICTs
  (mkargaki@redhat.com)
- Allow use S2I builder with non-s2i build strategies (mfojtik@redhat.com)
- Verify the integration test build early (ccoleman@redhat.com)
- Support building from dirs symlinked from GOPATH (pmorie@gmail.com)
- remove openshift ex tokens (deads@redhat.com)
- Improve Dockerfile keyword highlighting in web console (spadgett@redhat.com)
- Don't shutdown etcd in integration tests (ccoleman@redhat.com)
- hack/update-swagger-spec times out in integration (ccoleman@redhat.com)
- Dump debug info from etcd during integration tests (ccoleman@redhat.com)
- Create policy for image registry users (agladkov@redhat.com)
- Fill image's metadata in the registry (miminar@redhat.com)
- Added additional quota check for layer upload in a registry
  (miminar@redhat.com)
- Resource quota for images and image streams (miminar@redhat.com)
- Upgrade dind image to fedora23 (marun@redhat.com)
- Change button label from "Cancel" to "Cancel Build" (spadgett@redhat.com)
- Filter and sort web console events table (spadgett@redhat.com)
- Add header back to logging in page (spadgett@redhat.com)
- Add support for build config into oc set env (mfojtik@redhat.com)
- Fix timing problem enabling start build button (spadgett@redhat.com)
- Add Patternfly button styles to catalog browse button (spadgett@redhat.com)
- Bump Vagrant machine RAM requirement (dcbw@redhat.com)
- Remove json files added accidentally (rhcarvalho@gmail.com)
- Submit forms on enter (jhadvig@redhat.com)
- Set triggers via the CLI (ccoleman@redhat.com)
- UPSTREAM: <drop>: utility for the rolling updater (mkargaki@redhat.com)
- UPSTREAM: 21872: kubectl: preserve availability when maxUnavailability is not
  100%% (mkargaki@redhat.com)
- Including css declarations of flex specific prefixes for IE10 to position
  correctly (sgoodwin@redhat.com)
- Adjustments to the css controlling the filter widget so that it addresses
  some overlapping issues. Also, subtle changes to the project nav menu
  scrollbar so that it's more noticable. (sgoodwin@redhat.com)
- Only show builds bar chart when at least 4 builds (spadgett@redhat.com)
- Disable failing extended tests. (ccoleman@redhat.com)
- Remove v(4) logging of build admission startup (cewong@redhat.com)
- Include build hook in describer (rhcarvalho@gmail.com)
- Update hack/update-external-examples.sh (rhcarvalho@gmail.com)
- Update external examples (rhcarvalho@gmail.com)
- Add shasums to release build output (ccoleman@redhat.com)
- diagnostics: promote from openshift ex to oadm (lmeyer@redhat.com)
- Integrate etcd into the test cases themselves (ccoleman@redhat.com)
- UPSTREAM: 21265: added 'kubectl create sa' to create serviceaccounts
  (skuznets@redhat.com)
- Web console: improve repeated events message (spadgett@redhat.com)
- Improve web console metrics error message (spadgett@redhat.com)
- added generated swagger descriptions for v1 api (skuznets@redhat.com)
- Fix css compilation issues that affect IE, particularly flexbox
  (jforrest@redhat.com)
- pruned govet whitelist (skuznets@redhat.com)
- UPSTREAM: docker/distribution: 1474: Defined ErrAccessDenied error
  (miminar@redhat.com)
- UPSTREAM: docker/distribution: 1473: Commit uploaded blob with size
  (miminar@redhat.com)
- UPSTREAM: 20446: New features in ResourceQuota (miminar@redhat.com)
- Use args flavor sample-app build hooks (rhcarvalho@gmail.com)
- added automatic swagger doc generator (skuznets@redhat.com)
- Fix bindata diff (spadgett@redhat.com)
- disabling start build/rebuild button when bc is deleted (jhadvig@redhat.com)
- Add `oc debug` to make it easy to launch a test pod (ccoleman@redhat.com)
- Hide hidden flags in help output (ccoleman@redhat.com)
- React to changes in upstream term (ccoleman@redhat.com)
- UPSTREAM: 21624: improve terminal reuse and attach (ccoleman@redhat.com)
- Add 'oc set probe' for setting readiness and liveness (ccoleman@redhat.com)
- Remove npm shrinkwrap by bumping html-min deps (jforrest@redhat.com)
- Fix router e2e validation for docker 1.9 (marun@redhat.com)
- Cache projects outside of projectHeader link fn (admin@benjaminapetersen.me)
- Use $scope.$emit to notify projectHeader when project settings change
  (admin@benjaminapetersen.me)
- fix builder version typo (bparees@redhat.com)
- Update swagger description (jliggitt@redhat.com)
- add hostnetwork scc (pweil@redhat.com)
- UPSTREAM: 21680: Restore service port validation compatibility with 1.0/1.1
  (jliggitt@redhat.com)
- UPSTREAM: <carry>: change BeforeEach to JustBeforeEach to ensure SA is
  granted to anyuid SCC (pweil@redhat.com)
- Read extended user attributes from auth proxy (jliggitt@redhat.com)
- bump(github.com/openshift/openshift-sdn):
  08a79d5adc8af21b14adcc0b9650df2d5fccf2f0 (danw@redhat.com)
- Display better route info in status (ccoleman@redhat.com)
- Ensure log run vars are set in GET and WATCH on build, pod & deployment
  (admin@benjaminapetersen.me)
- Contextualize errors from GetCGroupLimits (rhcarvalho@gmail.com)
- Fix extended tests and up default pod limit. (ccoleman@redhat.com)
- configchange: abort update once an image change is detected
  (mkargaki@redhat.com)
- UPSTREAM: 21671: kubectl: add container ports in pod description
  (mkargaki@redhat.com)
- Fix reuse of release build on nfs mount (marun@redhat.com)
- Js error on overview for route warnings (jforrest@redhat.com)
- UPSTREAM: 21706: Ensure created service account tokens are available to the
  token controller (jliggitt@redhat.com)
- use imageid from trigger for imagesource inputs, instead of resolving them
  (bparees@redhat.com)
- increase binary build timeout to 5 minutes (bparees@redhat.com)
- Add status icon for ContainerCreating reason (spadgett@redhat.com)
- integration test for newapp dockerimagelookup (bparees@redhat.com)
- pod diagnostics: fix panic in bz 1302649, prettify (lmeyer@redhat.com)
- Fix log follow link on initial page load, add loading ellipsis while
  logViewer is pending (admin@benjaminapetersen.me)
- Don't show "Deployed" for plain RCs in web console (spadgett@redhat.com)
- Change default ClusterNetworkCIDR and HostSubnetLength (danw@redhat.com)
- Run post build hook with `/bin/sh -ic` (rhcarvalho@gmail.com)
- origin-pod rpm does not require the base rpm (sdodson@redhat.com)
- Updated copy-kube-artifacts to current k8s (maszulik@redhat.com)
- Mobile table headers missing on browse image page (jforrest@redhat.com)
- Suppress escape sequences at end of hack/test-assets.sh (ccoleman@redhat.com)
- Replace /bin/bash in oc rsh with /bin/sh (mfojtik@redhat.com)
- Remove downward api call for Jenkins kubernetes example (mfojtik@redhat.com)
- UPSTREAM: 19868: Fixed persistent volume claim controllers processing an old
  claim (jsafrane@redhat.com)
- Display better information when running 'oc' (ccoleman@redhat.com)
- Display additional tags after import (ccoleman@redhat.com)
- Update completions to be cross platform (ccoleman@redhat.com)
- Add events tab to plain RCs in web console (spadgett@redhat.com)
- new-app broken when docker not installed (ccoleman@redhat.com)
- UPSTREAM: 21628: Reduce node controller debug logging (ccoleman@redhat.com)
- Drop 1.4 and add 1.6 to travis Go matrix (ccoleman@redhat.com)
- Add --since-time logs test (jliggitt@redhat.com)
- UPSTREAM: 21398: Fix sinceTime pod log options (jliggitt@redhat.com)
- Show project display name in breadcrumbs (spadgett@redhat.com)
- Hide copy to clipboard button on iOS (spadgett@redhat.com)
- Validate master/publicMaster args to create-master-certs
  (jliggitt@redhat.com)
- Force dind deployment to build binaries by default (marun@redhat.com)
- Symlink repo mount to /origin for convenience (marun@redhat.com)
- Fix vagrant vm cluster and dind deployment (marun@redhat.com)
- Fix dind go build (marun@redhat.com)
- Update completions (ffranz@redhat.com)
- UPSTREAM: 21593: split adding global and external flags (ffranz@redhat.com)
- clean up wording of oc status build/deployment descriptions
  (bparees@redhat.com)
- iOS: prevent select from zooming page (spadgett@redhat.com)
- Restoring fix for route names overflowing .componet in Safari for iOS
  (rhamilto@redhat.com)
- On node startup, perform more checks of known requirements
  (ccoleman@redhat.com)
- Bug 1309195 - Return ErrNotV2Registry when falling back to http backend
  (maszulik@redhat.com)
- Set OS_OUTPUT_GOPATH=1 to build in a local GOPATH (ccoleman@redhat.com)
- Add back the filter bar to the bc and dc pages (jforrest@redhat.com)
- Router should tolerate not having permission to write status
  (ccoleman@redhat.com)
- Env vars with leading slashes cause major js errors in console create from
  image flow (jforrest@redhat.com)
- Refactor WaitForADeployment (rhcarvalho@gmail.com)
- bump(github.com/elazarl/goproxy): 07b16b6e30fcac0ad8c0435548e743bcf2ca7e92
  (ffranz@redhat.com)
- UPSTREAM: 21409: SPDY roundtripper support to proxy with Basic auth
  (ffranz@redhat.com)
- UPSTREAM: 21185: SPDY roundtripper must respect InsecureSkipVerify
  (ffranz@redhat.com)
- Bump docker minimum version to 1.9.1 in preparation for v1.2
  (sdodson@redhat.com)
- Use route ingress status in console (jforrest@redhat.com)
- correct cluster resource override tests (deads@redhat.com)
- UPSTREAM: 21268: Delete provisioned volumes without claim.
  (jsafrane@redhat.com)
- UPSTREAM: 21341: Add a liveness and readiness describer to pods
  (mkargaki@redhat.com)
- oc: enhance deploymentconfig description (mkargaki@redhat.com)
- Fix commit checker to find commits with upstream changes
  (jliggitt@redhat.com)
- Verify extended tests build (jliggitt@redhat.com)
- Fix extended build compile error (jliggitt@redhat.com)
- UPSTREAM: 21273: kubectl: scale down based on ready during rolling updates
  (mkargaki@redhat.com)
- Normalize usernames for AllowAllPasswordIdentityProvider
  (jliggitt@redhat.com)
- Add auth logging to login page, basic auth, and OAuth paths
  (jliggitt@redhat.com)
- Use "install" to install SDN script to make sure they get exec permission
  (danw@redhat.com)
- tar extract cannot hard link on vboxfs filesystem (horatiu@vlad.eu)
- Use pkg/util/homedir from upstream to detect home directory
  (ffranz@redhat.com)
- UPSTREAM: 17590: use correct home directory on Windows (ffranz@redhat.com)
- Web console: add "Completed" to status-icon directive (spadgett@redhat.com)
- refactored test-end-to-end/core to use os::cmd functions
  (skuznets@redhat.com)
- update completions (pweil@redhat.com)
- UPSTREAM: <carry>: add scc describer (pweil@redhat.com)
- Allow subdomain flag to create router (ccoleman@redhat.com)
- Adjust empty state margin for pages with tabs (spadgett@redhat.com)
- add gutter class to annotations directive to provide margin
  (admin@benjaminapetersen.me)
- vendor quickstart templates into origin (bparees@redhat.com)
- Add attach storage and create route to the actions dropdown
  (spadgett@redhat.com)
- properly check for nil docker client value (bparees@redhat.com)
- Web console: show more detailed pod status (spadgett@redhat.com)
- always pull the previous image for s2i builds (bparees@redhat.com)
- Improve log error messages (admin@benjaminapetersen.me)
- add DB icons and also add annotations to the 'latest' imagestream tags
  (bparees@redhat.com)
- Update and additions to web console screenshots (sgoodwin@redhat.com)
- Add Jenkins with kubernetes plugin example (mfojtik@redhat.com)
- UPSTREAM: 21470: fix limitranger to handle latent caches without live lookups
  every time (deads@redhat.com)
- react to limitrange update (deads@redhat.com)
- Handle multiple imageChange triggers in BC edit page (jhadvig@redhat.com)
- Resolving a couple cosmetic issues with navbar at mobile resolutions
  (rhamilto@redhat.com)
- Refactoring .component to prevent weird wrapping issues (rhamilto@redhat.com)
- UPSTREAM: 21335: make kubectl logs work for replication controllers
  (deads@redhat.com)
- make sure that logs for rc work correctly (deads@redhat.com)
- Use in-cluster-config without setting POD_NAMESPACE (jliggitt@redhat.com)
- UPSTREAM: 21095: Provide current namespace to InClusterConfig
  (jliggitt@redhat.com)
- Get rid of the plugins/ dir (ccoleman@redhat.com)
- Route ordering is unstable, and writes must be ignored (ccoleman@redhat.com)
- Replace kebab with actions button on browse pages (spadgett@redhat.com)
- Fixes for unnecessary scrollbars in certain areas and situations
  (sgoodwin@redhat.com)
- Fix asset build so that it leaves the dev environment in place without having
  to re-launch grunt serve (jforrest@redhat.com)
- addition of memory limits with online beta in mind (gmontero@redhat.com)
- make hello-openshift print to stdout when serving a request
  (bparees@redhat.com)
- Run-once pod duration: remove flag from plugin config (cewong@redhat.com)
- Limit route.spec.to to kind/name (jliggitt@redhat.com)
- Add deletecollection verb to admin/edit roles (jliggitt@redhat.com)
- UPSTREAM: 21005: Use a different verb for delete collection
  (jliggitt@redhat.com)
- Validate wildcard certs against non-wildcard namedCertificate names
  (jliggitt@redhat.com)
- Image building resets the global script time (ccoleman@redhat.com)
- remove volumes when removing containers (skuznets@redhat.com)
- UPSTREAM: 21089: Default lockfile to empty string while alpha
  (pweil@redhat.com)
- UPSTREAM: 21340: Tolerate individual NotFound errors in DeleteCollection
  (pweil@redhat.com)
- UPSTREAM: 21318: kubectl: use the factory properly for recording commands
  (pweil@redhat.com)
- refactor api interface to allow returning an error (pweil@redhat.com)
- fixing tests (pweil@redhat.com)
- proxy config refactor (pweil@redhat.com)
- boring refactors (pweil@redhat.com)
- UPSTREAM: <carry>: update generated client code for SCC (pweil@redhat.com)
- UPSTREAM: 21278: include discovery client in adaptor (pweil@redhat.com)
- bump(k8s.io/kubernetes): bc4550d9e93d04e391b9e33fc85a679a0ca879e9
  (pweil@redhat.com)
- UPSTREAM: openshift/openshift-sdn: <drop>: openshift-sdn refactoring
  (pweil@redhat.com)
- bump(github.com/stretchr/testify): e3a8ff8ce36581f87a15341206f205b1da467059
  (pweil@redhat.com)
- bump(github.com/onsi/ginkgo): 07d85e6b10c4289c7d612f9b13f45ba36f66d55b
  (pweil@redhat.com)
- bump(github.com/fsouza/go-dockerclient):
  0099401a7342ad77e71ca9f9a57c5e72fb80f6b2 (pweil@redhat.com)
- UPSTREAM: coreos/etcd: 4503: expose error details for normal stringify
  (deads@redhat.com)
- bump(github.com/coreos/etcd): bc9ddf260115d2680191c46977ae72b837785472
  (pweil@redhat.com)
- godeps: fix broken hash before restore (pweil@redhat.com)
- The Host value should be written to all rejected routes (ccoleman@redhat.com)
- fix jenkins testjob xml; fix jenkins ext test deployment error handling
  (gmontero@redhat.com)
- Web console: honor cluster-resource-override-enabled (spadgett@redhat.com)
- remove testing symlink (deads@redhat.com)
- Add pathseg polyfill to fix c3 bar chart runtime error (spadgett@redhat.com)
- Size build chart correctly in Firefox (spadgett@redhat.com)
- dump build logs when build test fails (bparees@redhat.com)
- fix circular input/output detection (bparees@redhat.com)
- do not tag for pushing if there is no output target (bparees@redhat.com)
- admission: cluster req/limit override plugin (lmeyer@redhat.com)
- ignore events from previous builds (bparees@redhat.com)
- Changes and additions to enable text truncation of the project menu and
  username at primary media query breakpoints (sgoodwin@redhat.com)
- Addition of top-header variables for mobile and desktop to set height and
  control offset of fixed header height.         This will ensure the proper
  bottom offset so that the flex containers extend to the bottom correctly.
  Switch margin-bottom to padding-bottom so that background color is maintained
  (sgoodwin@redhat.com)
- Set a timeout on integration tests of 4m (ccoleman@redhat.com)
- added support for paged queries in ldap sync (skuznets@redhat.com)
- bump(gopkg.in/ldap.v2): 07a7330929b9ee80495c88a4439657d89c7dbd87
  (skuznets@redhat.com)
- Resource specific events on browse pages (jhadvig@redhat.com)
- added Godoc to api types where Godoc was missing (skuznets@redhat.com)
- shorten dc caused by annotations (deads@redhat.com)
- bump(github.com/openshift/source-to-image):
  41947800efb9fb7f5c3a13e977d26ac0815fa4fb (maszulik@redhat.com)
- updated commitchecker regex to work for ldap package (skuznets@redhat.com)
- Fix layout in osc-key-value directive (admin@benjaminapetersen.me)
- bump(github.com/openshift/openshift-sdn):
  5cf5cd2666604324c3bd42f5c12774cfaf1a3439 (danw@redhat.com)
- Add docker-registry image store on glusterfs volume example
  (jcope@redhat.com)
- Bump travis to go1.5.3 (jliggitt@redhat.com)
- Provide a way in console to access orphaned builds / deployments
  (jforrest@redhat.com)
- Revising sidebar to better align with PatternFly standard
  (rhamilto@redhat.com)
- refactor docker image searching (bparees@redhat.com)
- added infra namespace to PV recycler (mturansk@redhat.com)
- UPSTREAM: 21266: only load kubeconfig files one time (deads@redhat.com)
- Run user-provided command as part of build flow (rhcarvalho@gmail.com)
- Fix deployment log var (admin@benjaminapetersen.me)
- Fix admission attribute comparison (agladkov@redhat.com)
- Remove EtcdClient from MasterConfig (agladkov@redhat.com)
- Add direnv .envrc to gitignore (pmorie@gmail.com)
- Move 'adm' function into 'oc' as 'oc adm' (ccoleman@redhat.com)
- Suppress conflict error printout (ccoleman@redhat.com)
- Break compile time dependency on etcd for clients (ccoleman@redhat.com)
- Use normal GOPATH for build (ccoleman@redhat.com)
- DeploymentConfig hooks did not have round trip defaulting
  (ccoleman@redhat.com)
- Fix pod warnings popup (spadgett@redhat.com)
- Move slow newapp tests to integration (ccoleman@redhat.com)
- filter events being tested (bparees@redhat.com)
- Improve performance of overview page with many deployments
  (spadgett@redhat.com)
- mark slow extended build/image tests (bparees@redhat.com)
- Tweak LDAP sync config error flags (jliggitt@redhat.com)
- Add extension points to the nav menus and add sample extensions for online
  (jforrest@redhat.com)
- UPSTREAM: coreos/etcd: 4503: expose error details for normal stringify
  (deads@redhat.com)
- UPSTREAM: 20213: Fixed persistent volume claim controllers processing an old
  volume (jsafrane@redhat.com)
- suppress query scope issue on member extraction (skuznets@redhat.com)
- use correct fixture path (bparees@redhat.com)
- Add a TagImages hook type to lifecycle hooks (ccoleman@redhat.com)
- Support create on update of imagestreamtags (ccoleman@redhat.com)
- Many anyuid programs fail due to SETGID/SETUID caps (ccoleman@redhat.com)
- Exclude failing tests, add [Kubernetes] and [Origin] skip targets
  (ccoleman@redhat.com)
- Scheduler has an official default name (ccoleman@redhat.com)
- Disable extended networking testing of services (marun@redhat.com)
- Fix filename of network test entry point (marun@redhat.com)
- Make sure extended networking isolation test doesn't run for subnet plugin
  (dcbw@redhat.com)
- Ensure more code uses the default transport settings (ccoleman@redhat.com)
- read docker pull secret from correct path (bparees@redhat.com)
- Ignore .vscode (ccoleman@redhat.com)
- Have routers take ownership of routes (ccoleman@redhat.com)
- Fix web console dev env certificate problems for OS X Chrome
  (spadgett@redhat.com)
- Update build info in web console pod template (spadgett@redhat.com)
- Changing .ace_editor to .ace_editor-bordered so the border around .ace_editor
  is optional (rhamilto@redhat.com)
- Web console: Warn about problems with routes (spadgett@redhat.com)
- fix variable shadowing complained about by govet for 1.4 (bparees@redhat.com)
- added LDIF for suppression testing (skuznets@redhat.com)
- launch integration tests using only the API server when possible
  (deads@redhat.com)
- bump(k8s.io/kubernetes): f0cd09aabeeeab1780911c8023203993fd421946
  (pweil@redhat.com)
- Create oscUnique directive to provide unique-in-list validation on DOM nodes
  with ng-model attribute (admin@benjaminapetersen.me)
- Support modifiable pprof web port (nakayamakenjiro@gmail.com)
- Add additional docker volume (dmcphers@redhat.com)
- Web console: Use service port name for route targetPort (spadgett@redhat.com)
- Correcting reference to another step (rhamilto@redhat.com)
- fix jobs package import naming (bparees@redhat.com)
- fix ldap sync decode codec (deads@redhat.com)
- Fix attachScrollEvents on window.resize causing affixed follow links in
  logViewer to behave inconsistently (admin@benjaminapetersen.me)
- Use SA config when creating clients (ironcladlou@gmail.com)
- fix up client code to use the RESTMapper functions they mean
  (deads@redhat.com)
- fix ShortcutRESTMapper and prevent it from ever silently failing again
  (deads@redhat.com)
- UPSTREAM: 20968: make partial resource detection work for singular matches
  (deads@redhat.com)
- UPSTREAM: 20829: Union rest mapper (deads@redhat.com)
- validate default imagechange triggers (bparees@redhat.com)
- ignore .vscode settings (jliggitt@redhat.com)
- handle additional cgroup file locations (bparees@redhat.com)
- Fix web console type error when image has no env (spadgett@redhat.com)
- Fixing livereload so that it works with https (rhamilto@redhat.com)
- Display source downloading in build logs by default (mfojtik@redhat.com)
- Clean up test scripts (jliggitt@redhat.com)
- Forging consistency among empty tables at xs screen size #7163
  (rhamilto@redhat.com)
- UPSTREAM: 20814: type RESTMapper errors to better handle MultiRESTMapper
  errors (deads@redhat.com)
- Renamed extended tests files by removing directory name from certain files
  (maszulik@redhat.com)
- oc: enable autoscale for dcs (mkargaki@redhat.com)
- add fuzzer tests for config scheme (deads@redhat.com)
- Add organization restriction to github IDP (jliggitt@redhat.com)
- Updates to use the SCC allowEmptyDirVolumePlugin setting.
  (dgoodwin@redhat.com)
- UPSTREAM: <carry>: scc (dgoodwin@redhat.com)
- UPSTREAM: <carry>: v1beta3 scc (dgoodwin@redhat.com)
- kebab case urls (and matching view templates), add legacy redirects
  (admin@benjaminapetersen.me)
- Add tests for explain (ccoleman@redhat.com)
- Bug fix where table border on right side of thead was disappearing at sm and
  md sizes (rhamilto@redhat.com)
- UPSTREAM: 20827: Backwards compat for old Docker versions
  (ccoleman@redhat.com)
- Cherrypick should force delete branch (ccoleman@redhat.com)
- Handle cert-writing error (jliggitt@redhat.com)
- Web console: only show "no services" message if overview empty
  (spadgett@redhat.com)
- Remove custom SIGQUIT handler (rhcarvalho@gmail.com)
- Support block profile by pprof webserver (nakayamakenjiro@gmail.com)
- Use the vendored KUBE_REPO_ROOT (ccoleman@redhat.com)
- Include Kube examples, needed for extended tests (rhcarvalho@gmail.com)
- Update copy-kube-artifacts.sh (rhcarvalho@gmail.com)
- Allow recursive DNS to be enabled (ccoleman@redhat.com)
- Return the Origin schema for explain (ccoleman@redhat.com)
- Regenerate conversions with stable order (ccoleman@redhat.com)
- UPSTREAM: 20847: Force a dependency order between extensions and api
  (ccoleman@redhat.com)
- UPSTREAM: 20858: Ensure public conversion name packages are imported
  (ccoleman@redhat.com)
- UPSTREAM: 20775: Set kube-proxy arg default values (jliggitt@redhat.com)
- Add kube-proxy config, match upstream proxy startup (jliggitt@redhat.com)
- allow either iptables-based or userspace-based proxy (danw@redhat.com)
- UPSTREAM: 20846: fix group mapping and encoding order: (deads@redhat.com)
- UPSTREAM: 20481: kubectl: a couple of edit fixes (deads@redhat.com)
- mark tests that access the host system as LocalNode (bparees@redhat.com)
- Build secrets isn't using fixture path (ccoleman@redhat.com)
- Test extended in parallel by default (ccoleman@redhat.com)
- UPSTREAM: 20796: SecurityContext tests wrong volume dir (ccoleman@redhat.com)
- UPSTREAM: 19947: Cluster DNS test is wrong (ccoleman@redhat.com)
- Replacing zeroclipboard with clipboard.js #5115 (rhamilto@redhat.com)
- import the AlwaysPull admission controller (pweil@redhat.com)
- GitLab IDP tweaks (jliggitt@redhat.com)
- BuildConfig editor fix (jhadvig@redhat.com)
- Tiny update in HACKING.md (nakayamakenjiro@gmail.com)
- Document requirements on kubernetes clone for cherry-picking.
  (jsafrane@redhat.com)
- Update recycler controller initialization. (jsafrane@redhat.com)
- Removing copyright leftovers (maszulik@redhat.com)
- UPSTREAM: 19365: Retry recycle or delete operation on failure
  (jsafrane@redhat.com)
- UPSTREAM: 19707: Fix race condition in cinder attach/detach
  (jsafrane@redhat.com)
- UPSTREAM: 19600: Fixed cleanup of persistent volumes. (jsafrane@redhat.com)
- example_test can fail due to validations (ccoleman@redhat.com)
- Add option and support for router id offset - this enables multiple
  ipfailover router installations to run within the same cluster. Rebased and
  changes as per @marun and @smarterclayton review comments.
  (smitram@gmail.com)
- Test extended did not compile (ccoleman@redhat.com)
- Unique host check should not delete when route is same (ccoleman@redhat.com)
- UPSTREAM: 20779: Take GVK in SwaggerSchema() (ccoleman@redhat.com)
- sanitize/consistentize how env variables are added to build pods
  (bparees@redhat.com)
- Update tag for Origin Kube (ccoleman@redhat.com)
- Fix typo (rhcarvalho@gmail.com)
- Add custom auth error template (jliggitt@redhat.com)
- fix multiple component error handling (bparees@redhat.com)
- Template test is not reentrant (ccoleman@redhat.com)
- Fix log viewer urls (jliggitt@redhat.com)
- make unit tests work (deads@redhat.com)
- make unit tests work (maszulik@redhat.com)
- eliminate v1beta3 round trip in the fuzzer.  We don't have to go out from
  there, only in (deads@redhat.com)
- move configapi back into its own scheme until we split the group
  (deads@redhat.com)
- refactor admission plugin types to avoid cycles and keep api types consistent
  (deads@redhat.com)
- update code generators (deads@redhat.com)
- make docker registry image auto-provisioning work with new status details
  (deads@redhat.com)
- add CLI helpers to convert lists before display since encoding no longer does
  it (deads@redhat.com)
- remove most of the latest package; it should go away completely
  (deads@redhat.com)
- template encoding/decoding no longer works like it used to (deads@redhat.com)
- add runtime.Object conversion method that works for now, but doesn't span
  groups or versions (deads@redhat.com)
- api type installation (deads@redhat.com)
- openshift launch sequence changed for rebase (deads@redhat.com)
- replacement etcd client (deads@redhat.com)
- oc behavior change by limiting generator scope (deads@redhat.com)
- runtime.EmbeddedObject removed (deads@redhat.com)
- scheme/codec changes (deads@redhat.com)
- API registration changes (deads@redhat.com)
- boring refactors for rebase (deads@redhat.com)
- UPSTREAM: 20736: clear env var check for unit test (deads@redhat.com)
- UPSTREAM: <drop>: make etcd error determination support old client until we
  drop it (deads@redhat.com)
- UPSTREAM: 20730: add restmapper String methods for debugging
  (deads@redhat.com)
- UPSTREAM: <drop>: disable kubelet image GC unit test (deads@redhat.com)
- UPSTREAM: 20648: fix validation error path for namespace (deads@redhat.com)
- UPSTREAM: <carry>: horrible hack for intstr types (deads@redhat.com)
- UPSTREAM: 20706: register internal types with scheme for reference unit test
  (deads@redhat.com)
- UPSTREAM: 20226:
  Godeps/_workspace/src/k8s.io/kubernetes/pkg/conversion/error.go
  (deads@redhat.com)
- UPSTREAM: 20511: let singularization handle non-conflicting ambiguity
  (deads@redhat.com)
- UPSTREAM: 20487: expose unstructured scheme as codec (deads@redhat.com)
- UPSTREAM: 20431: tighten api server installation for bad groups
  (deads@redhat.com)
- UPSTREAM: <drop>: patch for 16146: Fix validate event for non-namespaced
  kinds (deads@redhat.com)
- UPSTREAM: <drop>: merge multiple registrations for the same group
  (deads@redhat.com)
- UPSTREAM: emicklei/go-restful: <carry>: Add "Info" to go-restful ApiDecl
  (ccoleman@redhat.com)
- UPSTREAM: openshift/openshift-sdn: <drop>: minor updates for kube rebase
  (deads@redhat.com)
- UPSTREAM: docker/distribution: <carry>: remove parents on delete
  (miminar@redhat.com)
- UPSTREAM: docker/distribution: <carry>: export app.Namespace
  (miminar@redhat.com)
- UPSTREAM: docker/distribution: <carry>: custom routes/auth
  (agoldste@redhat.com)
- UPSTREAM: docker/distribution: 1050: Exported API functions needed for
  pruning (miminar@redhat.com)
- bump(k8s.io/kubernetes): 9da202e242d8ceedb549332fb31bf1a933a6c6b6
  (deads@redhat.com)
- bump(github.com/docker/docker): 0f5c9d301b9b1cca66b3ea0f9dec3b5317d3686d
  (deads@redhat.com)
- bump(github.com/coreos/go-systemd): b4a58d95188dd092ae20072bac14cece0e67c388
  (deads@redhat.com)
- bump(github.com/coreos/etcd): e0c7768f94cdc268b2fce31ada1dea823f11f505
  (deads@redhat.com)
- describe transitivity of bump commits (deads@redhat.com)
- clean godeps.json (deads@redhat.com)
- transitive bump checker (jliggitt@redhat.com)
- Clarify how to enable coverage report (rhcarvalho@gmail.com)
- Include offset of JSON syntax error (rhcarvalho@gmail.com)
- Move env and volume to a new 'oc set' subcommand (ccoleman@redhat.com)
- Make clean up before test runs more consistent (rhcarvalho@gmail.com)
- Prevent header and toolbar flicker for empty project (spadgett@redhat.com)
- Add GitLab OAuth identity provider (fabio@fh1.ch)
- release notes: incorrect field names will be rejected (pweil@redhat.com)
- Rename system:humans group to system:authenticated:oauth
  (jliggitt@redhat.com)
- Check index.docker.io/v1 when auth.docker.io/token has no auth
  (ccoleman@redhat.com)
- Update markup in chromeless templates to fix log scrolling issues
  (admin@benjaminapetersen.me)
- Adding missing bindata.go (rhamilto@redhat.com)
- Missing loading message on browse pages, only show tables on details tabs
  (jforrest@redhat.com)
- Set up API service and resourceGroupVersion helpers (jliggitt@redhat.com)
- Removing the transition on .sidebar-left for cleaner rendering on resize
  (rhamilto@redhat.com)
- Fix of project name alignment in IE, fixes bug 1304228 (sgoodwin@redhat.com)
- Test insecure TLS without CA for import (ccoleman@redhat.com)
- Admission control plugin to override run-once pod ActiveDeadlineSeconds
  (cewong@redhat.com)
- Fix problem with iOS zoom using the YAML editor (spadgett@redhat.com)
- Web console: editing compute resources limits (spadgett@redhat.com)
- Add cross project promotion example (mfojtik@redhat.com)
- Align edit build config styles with other edit pages (spadgett@redhat.com)
- Move build "rebuild" button to primary actions (spadgett@redhat.com)
- UPSTREAM: 16146: Fix validate event for non-namespaced kinds
  (deads@redhat.com)
- Bug 1304635: fix termination type for oc create route reencrypt
  (mkargaki@redhat.com)
- Bug 1304604: add missing route generator param for path (mkargaki@redhat.com)
- Support readiness checking on recreate strategy (ccoleman@redhat.com)
- Allow values as arguments in oc process (ffranz@redhat.com)
- Implement a mid hook for recreate deployments (ccoleman@redhat.com)
- Allow new-app to create test deployments (ccoleman@redhat.com)
- Force mount path to word break so it works at mobile (jforrest@redhat.com)
- Prevent dev cluster deploy from using stale config (marun@redhat.com)
- Bug fix:  adding Go installation step, formatting fix (rhamilto@redhat.com)
- Modify buildConfig from web console (jhadvig@redhat.com)
- made login fail with bad token (skuznets@redhat.com)
- Bug fixes:  broken link, formatting fixes, addition of missing step
  (rhamilto@redhat.com)
- Support test deployments (ccoleman@redhat.com)
- logs: return application logs for dcs (mkargaki@redhat.com)
- Constants in web console can be customized with JS extensions
  (ffranz@redhat.com)
- About page, configurable cli download links (ffranz@redhat.com)
- Preserve labels and annotations during reconcile scc (agladkov@redhat.com)
- Use tags consistently in top-level extended tests descriptions
  (mfojtik@redhat.com)
- Preserve existing oauth client secrets on startup (jliggitt@redhat.com)
- Bug 1298750 - Force IE document mode to be edge (jforrest@redhat.com)
- Only pass --ginkgo.skip when focus is absent (ccoleman@redhat.com)
- Unify new-app Resolver and Searcher (ccoleman@redhat.com)
- UPSTREAM: 20053: Don't duplicate error prefix (ccoleman@redhat.com)
- new-app should chase a defaulted "latest" tag to the stable ref
  (ccoleman@redhat.com)
- Update web console tab style (spadgett@redhat.com)
- apply builder pod cgroup limits to launched containers (bparees@redhat.com)
- Remove transition, no longer needed, that causes Safari mobile menu flicker
  https://github.com/openshift/origin/issues/6958 Remove extra alert from
  builds page Make spacing consistent by moving <h1>, actions, and labels into
  middle-header Add missing btn default styling to copy-to-clipboard
  (sgoodwin@redhat.com)
- Document how to run test/cmd tests in development (rhcarvalho@gmail.com)
- Use an insecure TLS config for insecure: true during import
  (ccoleman@redhat.com)
- Only load secrets if import needs them (ccoleman@redhat.com)
- Fix both header dropdowns staying open (jforrest@redhat.com)
- Add patching tests (jliggitt@redhat.com)
- Build defaults and build overrides admission plugins (cewong@redhat.com)
- Initial build http proxy admission control plugin (deads@redhat.com)
- Bug 1254431 - fix display of ICTs to handle the from subobject
  (jforrest@redhat.com)
- Bug 1275902 - fix help text for name field on create from image
  (jforrest@redhat.com)
- Fix display when build has not started, no startTimestamp exists
  (jforrest@redhat.com)
- Bug 1291535 - alignment of oc commands in next steps page is wrong
  (jforrest@redhat.com)
- Improve namer.GetName (rhcarvalho@gmail.com)
- Fix args check for role and scc modify (nakayamakenjiro@gmail.com)
- UPSTREAM: ugorji/go: <carry>: Fix empty list/map decoding
  (jliggitt@redhat.com)
- Updates to console theme (sgoodwin@redhat.com)
- Bug 1293578 - The Router liveness/readiness probes should always use
  localhost (bleanhar@redhat.com)
- handle .dockercfg and .dockerconfigjson independently (bparees@redhat.com)
- UPSTREAM: 19490: Don't print hairpin_mode error when not using Linux bridges
  (danw@gnome.org)
- ImageStreamImage returns incorrect image info (ccoleman@redhat.com)
- Replace NamedTagReference with TagReference (ccoleman@redhat.com)
- Don't fetch an is image if we are already in the process of fetching it
  (jforrest@redhat.com)
- Allow different version encoding for custom builds (nagy.martin@gmail.com)
- bump(github.com/openshift/source-to-image):
  f30208380974bdf302263c8a21b3e8a04f0bb909 (gmontero@redhat.com)
- Update java console to 1.0.42 (slewis@fusesource.com)
- UPSTREAM: 19366: Support rolling update to 0 desired replicas
  (dmace@redhat.com)
- added property deduping for junitreport (skuznets@redhat.com)
- Move graph helpers to deploy/api (ccoleman@redhat.com)
- oc: add `create route` subcommands (mkargaki@redhat.com)
- Allow images to be pulled through the Docker registry (ccoleman@redhat.com)
- Remove debug logging from project admission (ccoleman@redhat.com)
- Fixes #6797  - router flake due to some refactoring done. The probe needs an
  initial delay to allow the router to start up + harden the tests a lil' more
  by waiting for the router to come up and become available.
  (smitram@gmail.com)
- Improve godoc and add validation tests (ccoleman@redhat.com)
- Review 1 - Added indenting and more log info (ccoleman@redhat.com)
- Watch "run" change as part of watchGroup in logViewer to ensure logs run when
  ready (admin@benjaminapetersen.me)
- bump(github.com/openshift/source-to-image):
  91769895109ea8f193f41bc0e2eb6ba83b30a894 (mfojtik@redhat.com)
- remove unused flag (pweil@redhat.com)
- Add API Group to UI config (jliggitt@redhat.com)
- Add a customizable interstitial page to select login provider
  (jforrest@redhat.com)
- Update help for docker/config.json secrets (jliggitt@redhat.com)
- Bug 1303012 - Validate the build secret name in new-build
  (mfojtik@redhat.com)
- Add support for coalescing router reloads:   *  second implementation with a
  rate limiting function.   *  Fixes as per @eparis and @smarterclayton review
  comments.      Use duration instead of string/int values. This also updates
  the      usage to only allow values that time.ParseDuration accepts via
  either the infra router command line or via the RELOAD_INTERVAL
  environment variables. (smitram@gmail.com)
- bump(github.com/openshift/openshift-sdn):
  04aafc3712ec4d612f668113285370f58075e1e2 (maszulik@redhat.com)
- Update java console to 1.0.40 (slewis@fusesource.com)
- update kindToResource to match upstream (pweil@redhat.com)
- tweaks and explanation to use move-upstream.sh for rebase (deads@redhat.com)
- Delay fetching of logs on pod, build & deployment until logs are ready to run
  (admin@benjaminapetersen.me)
- bump(github.com/openshift/source-to-image):
  56dd02330716bd0ed94b87236a9989933b490237 (vsemushi@redhat.com)
- Fix js error in truncate directive (jforrest@redhat.com)
- make example imagesource path relative (bparees@redhat.com)
- remove grep -P usage (skuznets@redhat.com)
- Add a crashlooping error to oc status and a suggestion (ccoleman@redhat.com)
- Update the image import controller to schedule recurring import
  (ccoleman@redhat.com)
- oc: re-use edit from kubectl (mkargaki@redhat.com)
- oc: support `logs -p` for builds and deployments (mkargaki@redhat.com)
- api: enable serialization tests for Pod{Exec,Attach}Options
  (mkargaki@redhat.com)
- Project request quota admission control (cewong@redhat.com)
- Add environment to the relevant browse pages (jforrest@redhat.com)
- Make image stream import level driven (ccoleman@redhat.com)
- Add support to cli to set and display scheduled flag (ccoleman@redhat.com)
- Add a bucketed, rate-limited queue for periodic events (ccoleman@redhat.com)
- Allow admins to allow unlimited imported tags (ccoleman@redhat.com)
- Add server API config variables to control scheduling (ccoleman@redhat.com)
- API types for addition of scheduled to image streams (ccoleman@redhat.com)
- Update to fedora 23 (dmcphers@redhat.com)
- Edit project display name & description via settings page
  (admin@benjaminapetersen.me)
- UPSTREAM: <carry>: enable daemonsets by default (pweil@redhat.com)
- enable daemonset (pweil@redhat.com)
- oc: generate path-based routes in expose (mkargaki@redhat.com)
- Generated docs, swagger, completions, conversions (jliggitt@redhat.com)
- API group enablement for master/controllers (jliggitt@redhat.com)
- Explicit API version during login (jliggitt@redhat.com)
- API Group Version changes (maszulik@redhat.com)
- Make etcd registries consistent, updates for etcd test tooling changes
  (maszulik@redhat.com)
- API registration (maszulik@redhat.com)
- Change validation to use field.Path and field.ErrorList (maszulik@redhat.com)
- Determine PublicAddress automatically if masterIP is empty or loopback
  (jliggitt@redhat.com)
- Add origin client negotiation (jliggitt@redhat.com)
- Boring rebase changes (jliggitt@redhat.com)
- UPSTREAM: <drop>: Copy kube artifacts (jliggitt@redhat.com)
- UPSTREAM: 20157: Test specific generators for kubectl (jliggitt@redhat.com)
- UPSTREAM: <carry>: allow hostDNS to be included along with ClusterDNS setting
  (maszulik@redhat.com)
- UPSTREAM: 20093: Make annotate and label fall back to replace on patch
  compute failure (jliggitt@redhat.com)
- UPSTREAM: 19988: Fix kubectl annotate and label to use versioned objects when
  operating (maszulik@redhat.com)
- UPSTREAM: <carry>: Keep default generator for run 'run-pod/v1'
  (jliggitt@redhat.com)
- UPSTREAM: <drop>: stop registering versions in reverse order
  (jliggitt@redhat.com)
- UPSTREAM: 19892: Add WrappedRoundTripper methods to round trippers
  (jliggitt@redhat.com)
- UPSTREAM: 19887: Export transport constructors (jliggitt@redhat.com)
- UPSTREAM: 19866: Export PrintOptions struct (jliggitt@redhat.com)
- UPSTREAM: <carry>: remove types.generated.go (jliggitt@redhat.com)
- UPSTREAM: openshift/openshift-sdn: 253: update to latest client API
  (maszulik@redhat.com)
- UPSTREAM: emicklei/go-restful: <carry>: Add "Info" to go-restful ApiDecl
  (ccoleman@redhat.com)
- UPSTREAM: 17922: <partial>: Allow additional groupless versions
  (jliggitt@redhat.com)
- UPSTREAM: 20095: Restore LoadTLSFiles to client.Config (maszulik@redhat.com)
- UPSTREAM: 18653: Debugging round tripper should wrap CancelRequest
  (ccoleman@redhat.com)
- UPSTREAM: 18541: Allow node IP to be passed as optional config for kubelet
  (rpenta@redhat.com)
- UPSTREAM: <carry>: Tolerate node ExternalID changes with no cloud provider
  (sross@redhat.com)
- UPSTREAM: 19481: make patch call update admission chain after applying the
  patch (deads@redhat.com)
- UPSTREAM: revert: fa9f3ea88: coreos/etcd: <carry>: etcd is using different
  version of ugorji (jliggitt@redhat.com)
- UPSTREAM: 18083: Only attempt PV recycling/deleting once, else fail
  permanently (jliggitt@redhat.com)
- UPSTREAM: 19239: Added missing return statements (jliggitt@redhat.com)
- UPSTREAM: 18042: Add cast checks to controllers to prevent nil panics
  (jliggitt@redhat.com)
- UPSTREAM: 18165: fixes get --show-all (ffranz@redhat.com)
- UPSTREAM: 18621: Implement GCE PD dynamic provisioner. (jsafrane@redhat.com)
- UPSTREAM: 18607: Implement OpenStack Cinder dynamic provisioner.
  (jsafrane@redhat.com)
- UPSTREAM: 18601: Implement AWS EBS dynamic provisioner. (jsafrane@redhat.com)
- UPSTREAM: 18522: Close web socket watches correctly (jliggitt@redhat.com)
- UPSTREAM: 17590: correct homedir on windows (ffranz@redhat.com)
- UPSTREAM: 16964: Preserve int64 data when unmarshaling (jliggitt@redhat.com)
- UPSTREAM: <carry>: allow specific, skewed group/versions
  (jliggitt@redhat.com)
- UPSTREAM: 16667: Make HPA Controller use Namespacers (jliggitt@redhat.com)
- UPSTREAM: <carry>: OpenShift 3.0.2 nodes report v1.1.0-alpha
  (ccoleman@redhat.com)
- UPSTREAM: 16067: Provide a RetryOnConflict helper for client libraries
  (maszulik@redhat.com)
- UPSTREAM: 12221: Allow custom namespace creation in e2e framework
  (deads@redhat.com)
- UPSTREAM: 15451: <partial>: Add our types to kubectl get error
  (ccoleman@redhat.com)
- UPSTREAM: <carry>: add kubelet timeouts (maszulik@redhat.com)
- UPSTREAM: 8890: Allowing ActiveDeadlineSeconds to be updated for a pod
  (maszulik@redhat.com)
- UPSTREAM: <carry>: tweak generator to handle conversions in other packages
  (deads@redhat.com)
- UPSTREAM: <carry>: Suppress aggressive output of warning
  (ccoleman@redhat.com)
- UPSTREAM: <carry>: v1beta3 (deads@redhat.com)
- UPSTREAM: <carry>: support pointing oc exec to old openshift server
  (deads@redhat.com)
- UPSTREAM: <carry>: Back n forth downward/metadata conversions
  (deads@redhat.com)
- UPSTREAM: <carry>: update describer for dockercfg secrets (deads@redhat.com)
- UPSTREAM: <carry>: reallow the ability to post across namespaces in api
  (pweil@redhat.com)
- UPSTREAM: <carry>: Add deprecated fields to migrate 1.0.0 k8s v1 data
  (jliggitt@redhat.com)
- UPSTREAM: <carry>: SCC (deads@redhat.com)
- UPSTREAM: <carry>: Disable UIs for Kubernetes and etcd (deads@redhat.com)
- bump(github.com/openshift/openshift-sdn):
  eda3808d8fe615229f168661fea021a074a34750 (jliggitt@redhat.com)
- bump(github.com/ugorji/go): f1f1a805ed361a0e078bb537e4ea78cd37dcf065
  (maszulik@redhat.com)
- bump(github.com/emicklei/go-restful):
  777bb3f19bcafe2575ffb2a3e46af92509ae9594 (maszulik@redhat.com)
- bump(github.com/coreos/go-systemd): 97e243d21a8e232e9d8af38ba2366dfcfceebeba
  (maszulik@redhat.com)
- bump(github.com/coreos/go-etcd): 003851be7bb0694fe3cc457a49529a19388ee7cf
  (maszulik@redhat.com)
- bump(k8s.io/kubernetes): 4a65fa1f35e98ae96785836d99bf4ec7712ab682
  (jliggitt@redhat.com)
- fix sample usage (bparees@redhat.com)
- Disable replication testing for MySQL 5.5 (nagy.martin@gmail.com)
- Install iptables-services for dev & dind clusters (marun@redhat.com)
- Check for forbidden error on ImageStreamImport client (cewong@redhat.com)
- Sanitize S2IBuilder tests (rhcarvalho@gmail.com)
- Add container from annotations to options for build log to generate kibana
  url (admin@benjaminapetersen.me)
- status: Report path-based passthrough terminated routes (mkargaki@redhat.com)
- Add extended test for MongoDB. (vsemushi@redhat.com)
- Simplify Makefile for limited parallelization (ccoleman@redhat.com)
- If release binaries exist, extract them instead of building
  (ccoleman@redhat.com)
- Webhooks: use constant-time string secret comparison (elyscape@gmail.com)
- bump(github.com/openshift/source-to-image):
  78f4e4fe283bd9619804da9e929c61f655df6d06 (bparees@redhat.com)
- Send error output from verify-gofmt to stderr to allow piping to xargs to
  clean up (jliggitt@redhat.com)
- Implement submodule init/update in s2i (christian@paral.in)
- guard openshift resource dump (skuznets@redhat.com)
- Add endpoints to oc describe route (agladkov@redhat.com)
- Use docker registry contants (miminar@redhat.com)
- deployapi: remove obsolete templateRef reference (mkargaki@redhat.com)
- Do not remove image after Docker build (rhcarvalho@gmail.com)
- If Docker is installed, run the e2e/integ variant automatically
  (ccoleman@redhat.com)
- UPSTREAM: <drop>: (do not merge) Make upstream tests pass on Mac
  (ccoleman@redhat.com)
- test/cmd/basicresources.sh fails on macs (ccoleman@redhat.com)
- Remove Travis + assets workarounds (ccoleman@redhat.com)
- Implement authenticated image import (ccoleman@redhat.com)
- refactored test-cmd core to use os::cmd functions (skuznets@redhat.com)
- Move limit range help text outside of header on settings page
  (spadgett@redhat.com)
- hello-openshift example: make the ports configurable (v.behar@free.fr)
- new-build support for image source (cewong@redhat.com)
- bump(github.com/blang/semver):31b736133b98f26d5e078ec9eb591666edfd091f
  (ccoleman@redhat.com)
- Do not retry if the UID changes on import (ccoleman@redhat.com)
- Make import-image a bit more flexible (ccoleman@redhat.com)
- UPSTREAM: <drop>: Allow client transport wrappers to support CancelRequest
  (ccoleman@redhat.com)
-  bump(github.com/fsouza/go-dockerclient)
  25bc220b299845ae5489fd19bf89c5278864b050 (bparees@redhat.com)
- restrict project requests to human users: ones with oauth tokens
  (deads@redhat.com)
- Improve display of quota and limits in web console (spadgett@redhat.com)
- cmd tests: fix diagnostics tests (lmeyer@redhat.com)
- Allow --all-namespaces on status (ccoleman@redhat.com)
- don't fail for parsing error (pweil@redhat.com)
- accept diagnostics as args (deads@redhat.com)
- mark validation commands as deprecated (skuznets@redhat.com)
- fix template processing (deads@redhat.com)
- deployapi: make dc selector optional (mkargaki@redhat.com)
- Not every registry has library (miminar@redhat.com)
- reverted typo in extended cmd (skuznets@redhat.com)
- Set REGISTRY_HTTP_SECRET (agladkov@redhat.com)
- homogenize tmpdirs (skuznets@redhat.com)
- Add support for --build-secret to oc new-build command (mfojtik@redhat.com)
- WIP: Add extended test for source build secrets (mfojtik@redhat.com)
- Allow to specify secrets used for the build in source (vsemushi@redhat.com)
- Fixed typo in junitreport properties (maszulik@redhat.com)
- Suppress tooltip when hovering over cut-line at top of pod donut
  (spadgett@redhat.com)
- Support debugging networking tests with delve (marun@redhat.com)
- Described oadm prune builds command. (vsemushi@redhat.com)
- Block build cloning when BC is paused (nagy.martin@gmail.com)
- cleanup of extended cleanup traps (deads@redhat.com)
- oadm: should have prune groups cmd (mkargaki@redhat.com)
- Improve message for deprecated build-logs option. (vsemushi@redhat.com)
- bump(github.com/openshift/openshift-sdn)
  fccee2120e9e8662639df6b40f4e1adf07872105 (danw@redhat.com)
- Set REGISTRY_HTTP_ADDR to first specified port (agladkov@redhat.com)
- ignore ctags file (ian.miell@gmail.com)
- Initial addition of image promotion proposal (mfojtik@redhat.com)
- oadm: bump prune deployments description/examples (mkargaki@redhat.com)
- Add annotation information when describing new-app results
  (ccoleman@redhat.com)
- made system logger get real error code (skuznets@redhat.com)
- wire an etcd dump into an API server for debugging (deads@redhat.com)
- add extended all.sh to allow [extended:all] to run all buckets
  (deads@redhat.com)
- diagnostics: add diagnostics from pod perspective (lmeyer@redhat.com)
- Use interfaces to pass config data to admission plugins (cewong@redhat.com)
- Create registry dc with readiness probe (miminar@redhat.com)
- removed global project cache (skuznets@redhat.com)
- Improve data population (ccoleman@redhat.com)
- stop status from checking SA mountable secrets (deads@redhat.com)
- remove outdated validation (skuznets@redhat.com)
- return a error+recommendation to the user on multiple matches, prioritize
  imagestream matches over annotation matches (bparees@redhat.com)
- make test-integration use our etcd (deads@redhat.com)
- Updated troubleshooting guide with information about insecure-registry
  (maszulik@redhat.com)
- DuelingRepliationControllerWarning -> DuelingReplicationControllerWarning
  (ian.miell@gmail.com)
- Updated generated docs (miminar@redhat.com)
- Fix hack/test-go.sh testing packages recursively (jliggitt@redhat.com)
- Expose admission control plugins list and config in master configuration
  (cewong@redhat.com)
- put openshift-f5-router in origin.spec (tdawson@redhat.com)
- add etcdserver launch mechanism (deads@redhat.com)
- Update minimum Docker version (rhcarvalho@gmail.com)
- added system logging utility (skuznets@redhat.com)
- Described oadm prune images command (miminar@redhat.com)
- add caps defaulting (pweil@redhat.com)
- hack/move-upstream now supports extracting true commits (ccoleman@redhat.com)
- bump(github.com/openshift/source-to-image):
  8ec5b0f51f8baa30159c1d8cceb62126bba6f384 (mfojtik@redhat.com)
- bump(fsouza/go-dockerclient): 299d728486342c894e7fafd68e3a4b89623bef1d
  (mfojtik@redhat.com)
- Update lodash to v 3.10.1 (admin@benjaminapetersen.me)
- Implement BuildConfig reaper (nagy.martin@gmail.com)
- clarify build-started message based on buildconfig triggers
  (bparees@redhat.com)
- Lock bootstrap-hover-dropdown version to 2.1.3 (spadgett@redhat.com)
- Lock ace-builds version to 1.2.2 (spadgett@redhat.com)
- Enable swift storage backend for the registry (miminar@redhat.com)
- bump(ncw/swift): c54732e87b0b283d1baf0a18db689d0aea460ba3
  (miminar@redhat.com)
- Enable cloudfront storage driver in dockerregistry (miminar@redhat.com)
- bump(AdRoll/goamz/cloudfront): aa6e716d710a0c7941cb2075cfbb9661f16d21f1
  (miminar@redhat.com)
- Use const values as string for defaultLDAP(S)Port (nakayamakenjiro@gmail.com)
- Fix up net.bridge.bridge-nf-call-iptables after kubernetes breaks it
  (danw@redhat.com)
- admission tests and swagger (pweil@redhat.com)
- UPSTREAM: <carry>: capability defaulting (pweil@redhat.com)
- Fix logic to add Dockerfile to BuildConfig (rhcarvalho@gmail.com)
- Do not check builds/details in build by strategy admission control
  (cewong@redhat.com)
- Replace --master option with --config (miminar@redhat.com)
- Add TIMES=N to rerun integration tests for flakes (ccoleman@redhat.com)
- Fix route serialization flake (mkargaki@redhat.com)
- STI -> S2I (dmcphers@redhat.com)
- Enable Azure Blob Storage (spinolacastro@gmail.com)
- bump(Azure/azure-sdk-for-go/storage):
  97d9593768bbbbd316f9c055dfc5f780933cd7fc (spinolacastro@gmail.com)
- Fix typo in build generator (mfojtik@redhat.com)
- bump(github.com/openshift/openshift-sdn)
  eda3808d8fe615229f168661fea021a074a34750 (dcbw@redhat.com)
- Auto generated bash completions for node-ip kubelet config option
  (rpenta@redhat.com)
- Use KubeletServer.NodeIP instead of KubeletServer.HostnameOverride to set
  node IP (rpenta@redhat.com)
- UPSTREAM: <carry>: Tolerate node ExternalID changes with no cloud provider
  (sross@redhat.com)
- Update certs for router tests (jliggitt@redhat.com)
- Retry adding roles to service accounts in conflict cases
  (jliggitt@redhat.com)
- Include update operation in build admission controller (cewong@redhat.com)
- UPSTREAM: 18541: Allow node IP to be passed as optional config for kubelet
  (rpenta@redhat.com)
- Fix test fixture fields (mkargaki@redhat.com)
- Simplify reading of random bytes (rhcarvalho@gmail.com)
- Make `oc cancel-build` to be suggested for `oc stop-build`.
  (vsemushi@redhat.com)
- Wait for access tokens to be available in clustered etcd
  (jliggitt@redhat.com)
- Add a new image to be used for testing (ccoleman@redhat.com)
- Fix kill_all_processes on OS X (cewong@redhat.com)
- The default codec should be v1.Codec, not v1beta3 (ccoleman@redhat.com)
- Bug 1263609 - fix oc rsh usage (ffranz@redhat.com)
- Fix HPA default policy (jliggitt@redhat.com)
- oc rsync: expose additional rsync flags (cewong@redhat.com)
- Bug 1248463 - fixes exec help (ffranz@redhat.com)
- Bug 1273708 - mark --all in oc export deprecated in help (ffranz@redhat.com)
- Enable PostgreSQL replication tests for RHEL images (nagy.martin@gmail.com)
- Fix tests for route validation changes (mkargaki@redhat.com)
- Make new-build output BC with multiple sources (rhcarvalho@gmail.com)
- Remove code duplication (rhcarvalho@gmail.com)
- Require tls termination in route tls configuration (mkargaki@redhat.com)
- Fix nw extended test support for skipping build (marun@redhat.com)
- Fix broken switch in usageWithUnits filter (spadgett@redhat.com)
- UPSTREAM: 19481: make patch call update admission chain after applying the
  patch (deads@redhat.com)
- diagnostics: logs and units for origin (lmeyer@redhat.com)
- Update java console to 1.0.39 (slewis@fusesource.com)
- extended tests for jenkins openshift V3 plugin (gmontero@redhat.com)
- bump(github.com/openshift/openshift-sdn)
  da8ad5dc5c94012eb222221d909b2b6fa678500f (dcbw@redhat.com)
- Update for openshift-sdn script installation changes (danw@redhat.com)
- use direct mount for etcd data (deads@redhat.com)
- mark image input source as experimental (bparees@redhat.com)
- made large file behavior smarter (skuznets@redhat.com)
- Revert "Allow parallel image stream importing" (jordan@liggitt.net)
- Fix deployment CLI ops link and make all doc links https
  (jforrest@redhat.com)
- Fix detection of Python projects (rhcarvalho@gmail.com)
- add probe for mongodb template (haowang@redhat.com)
- deal with RawPath field added to url.URL in go1.5 (gmontero@redhat.com)
- Include kube e2e service tests in networking suite (marun@redhat.com)
- Fix replication controller usage in kube e2e tests (marun@redhat.com)
- Enable openshift-sdn sdn node by default (marun@redhat.com)
- Fix dind compatibility with centos/rhel (marun@redhat.com)
- Fix dind compatibility with centos/rhel (marun@redhat.com)
- added junitreport tool (skuznets@redhat.com)
- diagnostics: list diagnostic names in long desc (lmeyer@redhat.com)
- Increase web console e2e login timeout (spadgett@redhat.com)
- Persistent volume claims on the web console (ffranz@redhat.com)
- add option --insecure for oc import-image
  (haoran@dhcp-129-204.nay.redhat.com)
- update extended test to point to correct version tool (skuznets@redhat.com)
- add warning about root user in images (bparees@redhat.com)
- new-app: search local docker daemon if registry search fails
  (cewong@redhat.com)
- Fix breadcrumb on next steps page (spadgett@redhat.com)
- Enable DWARF debuginfo (tdawson@redhat.com)
- update scripts to respect TMPDIR (deads@redhat.com)
- stop etcd from retrying failures (deads@redhat.com)
- allow parallel image streams (deads@redhat.com)
- created structure for whitelisting directories for govet shadow testing
  (skuznets@redhat.com)
- handle missing dockerfile with docker strategy (bparees@redhat.com)
- Bump kubernetes-topology-graph to 0.0.21 (spadgett@redhat.com)
- Print more enlightening string if test fails (rhcarvalho@gmail.com)
- Add to project catalog legend and accessibility fixes (spadgett@redhat.com)
- tolerate spurious failure during test setup (deads@redhat.com)
- fixed readiness endpoint route listing (skuznets@redhat.com)
- moved tools from cmd/ to tools/ (skuznets@redhat.com)
- Fix scale up button tooltip (spadgett@redhat.com)
- fix deploy test to use actual master (deads@redhat.com)
- Use angular-bootstrap dropdown for user menu (spadgett@redhat.com)
- added bash autocompletion for ldap sync config (skuznets@redhat.com)
- Suppress conflict error logging when adding SA role bindings
  (jliggitt@redhat.com)
- Don't allow clock icon to wrap in image tag table (spadgett@redhat.com)
- diagnostics: improve wording of notes (lmeyer@redhat.com)
- diagnostics: improve master/node config warnings (lmeyer@redhat.com)
- Show scalable deployments on web console overview even if not latest
  (spadgett@redhat.com)
- Use angular-bootstrap uib-prefixed components (spadgett@redhat.com)
- write output to file in e2e core (skuznets@redhat.com)
- Make web console alerts dismissable (spadgett@redhat.com)
- Reenabled original registry's /healthz route (miminar@redhat.com)
- fixed TestEditor output (skuznets@redhat.com)
- added readiness check to LDAP server pod (skuznets@redhat.com)
- diagnostics: avoid some redundancy (lmeyer@redhat.com)
- update auth tests to use actual master (deads@redhat.com)
- declared variables better for RHEL (skuznets@redhat.com)
- fix non-compliant build integration tests (deads@redhat.com)
- BuildConfig envVars in wrong structure in sti build template
  (jhadvig@redhat.com)
- Remove unnecessary type conversions (rhcarvalho@gmail.com)
- Wait until animation finishes to call chart.flush() (spadgett@redhat.com)
- oc: Add more doc and examples in oc get (mkargaki@redhat.com)
- Make KUBE_TIMEOUT take a duration (rhcarvalho@gmail.com)
- examples: Update resource quota README (mkargaki@redhat.com)
- promoted group prune and sync from experimental (skuznets@redhat.com)
- Various accessibility fixes, bumps angular-bootstrap version
  (jforrest@redhat.com)
- Avoid scrollbar flicker on build trends tooltip (spadgett@redhat.com)
- Show empty RCs in some cases on overview when no service
  (spadgett@redhat.com)
- make os::cmd::try_until* output smarter (skuznets@redhat.com)
- Fix tito ldflag manipulation at tag time (sdodson@redhat.com)
- graphapi: Remove dead code and add godoc (mkargaki@redhat.com)
- describe DockerBuildStrategy.DockerfilePath (v.behar@free.fr)
- integration-tests: retry get image on not found error (miminar@redhat.com)
- Adapt to etcd changes from v2.1.2 to v2.2.2 (ccoleman@redhat.com)
- UPSTREAM: coreos/etcd: <carry>: etcd is using different version of ugorji
  (ccoleman@redhat.com)
- bump(github.com/coreos/etcd):b4bddf685b26b4aa70e939445044bdeac822d042
  (ccoleman@redhat.com)
- Fix oc status unit test (mkargaki@redhat.com)
- Wait for user permissions in test-cmd.sh (jliggitt@redhat.com)
- Wait for bootstrap policy on startup (jliggitt@redhat.com)
- Shorten image importer dialTimeout to 5 seconds (jliggitt@redhat.com)
- Improve web console scaling (spadgett@redhat.com)
- Increase specificity of CSS .yaml-mode .ace-numeric style
  (spadgett@redhat.com)
- UPSTREAM: <drop>: fixup for 14537 (mturansk@redhat.com)
- Add bash auto-completion for oc, oadm, and openshift to the environments
  created by Vagrant. (bbennett@redhat.com)
- Fix github link when contextDir is set but not git ref (jforrest@redhat.com)
- install which in the base image (bparees@redhat.com)
- UPSTREAM: 18165: fixes get --show-all (ffranz@redhat.com)
- fix extra indentation for bare builds (deads@redhat.com)
- bump(AdRoll/goamz): aa6e716d710a0c7941cb2075cfbb9661f16d21f1
  (miminar@redhat.com)
- Edit resource YAML in the web console (spadgett@redhat.com)
- Use DeepEqual instead of field by field comparison (rhcarvalho@gmail.com)
- Fix regression: new-app with custom Git ref (rhcarvalho@gmail.com)
- Fix typo in example `oc run` command. (dusty@dustymabe.com)
- Increase debug logging for image import controller (jliggitt@redhat.com)
- Gather logs for test-cmd (jliggitt@redhat.com)
- deployapi: Necessary refactoring after updating the internal objects
  (mkargaki@redhat.com)
- UPSTREAM: 18621: Implement GCE PD dynamic provisioner. (jsafrane@redhat.com)
- UPSTREAM: 17747: Implement GCE PD disk creation. (jsafrane@redhat.com)
- UPSTREAM: 18607: Implement OpenStack Cinder dynamic provisioner.
  (jsafrane@redhat.com)
- UPSTREAM: 18601: Implement AWS EBS dynamic provisioner. (jsafrane@redhat.com)
- Fix test-cmd.sh on OSX (jliggitt@redhat.com)
- Web console: Fix edge case scaling to 0 replicas (spadgett@redhat.com)
- correctly determine build pushability for status (deads@redhat.com)
- move imagestream creation to more sensible spot (bparees@redhat.com)
- Avoid generating tokens with leading dashes (jliggitt@redhat.com)
- deployapi: Update generated conversions and deep copies (mkargaki@redhat.com)
- deployapi: Update manual conversions (mkargaki@redhat.com)
- deployapi: Refactor internal objects to match versioned (mkargaki@redhat.com)
- Show 'none' when there is no builder image. (rhcarvalho@gmail.com)
- status: Add more details for a broken dc trigger (mkargaki@redhat.com)
- diagnose timeouts correctly in error message (skuznets@redhat.com)
- Allow using an image as source for a build (cewong@redhat.com)
- Fix up ClusterNetwork validation. (danw@redhat.com)
- Show warning when --env is used in start-build with binary source
  (mfojtik@redhat.com)
- Fix deployements/stragies anchor link (christophe@augello.be)
- don't output empty strings in logs (bparees@redhat.com)
- bump(github.com/openshift/openshift-sdn)
  e7f0d8be285f73c896ff19455bd03d5189cbe5e6 (dcbw@redhat.com)
- Fix race between Kubelet initialization and plugin creation (dcbw@redhat.com)
- Output more helpful cancel message (jliggitt@redhat.com)
- Use the iptables-based proxier instead of the userland one (danw@redhat.com)
- Delete tag if its history is empty (miminar@redhat.com)
- Remove redundant admin routes (miminar@redhat.com)
- Reenabled registry dc's liveness probe (miminar@redhat.com)
- Refactor of OSO's code (miminar@redhat.com)
- Refactor dockerregistry: prevent a warning during startup
  (miminar@redhat.com)
- Refactor dockerregistry: unify logging style with upstream's codebase
  (miminar@redhat.com)
- Refactor dockerregistry: use registry's own health check (miminar@redhat.com)
- Refactor dockerregistry: adapt to upstream changes (miminar@redhat.com)
- Registry refactor: handle REGISTRY_CONFIGURATION_PATH (miminar@redhat.com)
- unbump(code.google.com/p/go-uuid/uuid): which is obsoleted
  (miminar@redhat.com)
- Always use port 53 as the dns service port. (abutcher@redhat.com)
- Fix service link on route page (spadgett@redhat.com)
- Increase contrast of web console log text (spadgett@redhat.com)
- custom Dockerfile path for the docker build (v.behar@free.fr)
- assets: Fix up the topology view icon colors and lines (stefw@redhat.com)
- Remove static nodes, deprecate --nodes (jliggitt@redhat.com)
- Add PV Provisioner Controller (mturansk@redhat.com)
- Fix for bugz https://bugzilla.redhat.com/show_bug.cgi?id=1290643   o Make
  Forwarded header value rfc7239 compliant.   o Set X-Forwarded-Proto for http
  (if insecure edge terminated routes     are allowed). (smitram@gmail.com)
- UPSTREAM: 14537: Add PersistentVolumeProvisionerController
  (mturansk@redhat.com)
- Fix test failures for scoped and host-overriden routers. (smitram@gmail.com)
- Unit test for hostname override (ccoleman@redhat.com)
- Routers should be able to override the host value on Routes
  (ccoleman@redhat.com)
- added os::cmd readme (skuznets@redhat.com)
- added support for recursive testing using test-go (skuznets@redhat.com)
- fixed group detection bug for LDAP prune (skuznets@redhat.com)
- removed tryuntil from test-cmd (skuznets@redhat.com)
- fixed LDAP test file extensions (skuznets@redhat.com)
- Allow image importing to work with proxy (jkhelil@gmail.com)
- oc: Use object name instead of provided arg in cancel-build
  (mkargaki@redhat.com)
- add step for getting the jenkins service ip (bparees@redhat.com)
- fix forcepull setup build config (gmontero@redhat.com)
- Add user/group reapers (jliggitt@redhat.com)
- Make project template use default rolebinding name (jliggitt@redhat.com)
- update missing imagestream message to warning (bparees@redhat.com)
- Temporary fix for systemd upgrade path issues (sdodson@redhat.com)
- Add logging for etcd integration tests (jliggitt@redhat.com)
- Fix the mysql replica extended test (mfojtik@redhat.com)
- Use service port name as route targetPort in 'oc expose service'
  (jliggitt@redhat.com)
- Refactor SCM auth and use of env vars in builders (cewong@redhat.com)
- oc: Cosmetic fixes in oc status (mkargaki@redhat.com)
- allow for test specification from command-line for test-cmd
  (skuznets@redhat.com)
- fixed caching bug in ldap sync (skuznets@redhat.com)
- Include LICENSE in client zips (ccoleman@redhat.com)
- Change uuid imports to github.com/pborman/uuid (miminar@redhat.com)
- UPSTREAM: docker/distribution: <carry>: remove parents on delete
  (miminar@redhat.com)
- UPSTREAM: docker/distribution: <carry>: export app.Namespace
  (miminar@redhat.com)
- UPSTREAM: docker/distribution: <carry>: custom routes/auth
  (agoldste@redhat.com)
- UPSTREAM: docker/distribution: 1050: Exported API functions needed for
  pruning (miminar@redhat.com)
- bump(github.com/stevvooe/resumable): 51ad44105773cafcbe91927f70ac68e1bf78f8b4
  (miminar@redhat.com)
- bump(github.com/docker/distribution):
  e6c60e79c570f97ef36f280fcebed497682a5f37 (miminar@redhat.com)
- Give user suggestion about new-app on new-project (ccoleman@redhat.com)
- Controllers should always go async on start (ccoleman@redhat.com)
- Minor commit validation fixes (ironcladlou@gmail.com)
- remove build-related type fields from internal api (bparees@redhat.com)
- Add godeps commit verification (ironcladlou@gmail.com)
- update deltafifo usage to match upstream changes (bparees@redhat.com)
- Retry build logs in start build when waiting for build (mfojtik@redhat.com)
- Create proper client packages for mac and windows (ccoleman@redhat.com)
- update jenkins tutorial for using plugin (gmontero@redhat.com)
- Allow oc new-build to accept zero arguments (ccoleman@redhat.com)
- Fix fallback scaling behavior (ironcladlou@gmail.com)
- Fix deployment e2e flake (mkargaki@redhat.com)
- UPSTREAM: 18522: Close web socket watches correctly (jliggitt@redhat.com)
- bump(github.com/openshift/openshift-sdn)
  8a7e17c0c3eea529955229dfd7b4baefad56633b (rpenta@redhat.com)
- Start SDN controller after running kubelet (rpenta@redhat.com)
- [RPMs] Cleanup kubeplugin path from old sdn-ovs installs (sdodson@redhat.com)
- Fix flakiness in builds extended tests (cewong@redhat.com)
- Add suggestions in oc status (mkargaki@redhat.com)
- status: Report tls routes with unspecified termination type
  (mkargaki@redhat.com)
- Use the dockerclient ClientFromEnv setup (ccoleman@redhat.com)
- Don't show build trends chart scrollbars if not needed (spadgett@redhat.com)
- Prevent y-axis label overlap when filtering build trends chart
  (spadgett@redhat.com)
- Packaging specfile clean up (admiller@redhat.com)
- added prune-groups; refactored rfc2307 ldapinterface (skuznets@redhat.com)
- only expand resources when strictly needed (deads@redhat.com)
- added logging of output for failed builds (ipalade@redhat.com)
- bump(github.com/openshift/openshift-sdn)
  0f33df18b9747ebfe2c337f2bf4443b520a8f2ab (rpenta@redhat.com)
- UPSTREAM: revert: 97bd6c: <carry>: Allow pod start to be delayed in Kubelet
  (rpenta@redhat.com)
- Don't use KubeletConfig 'StartUpdates' channel for blocking kubelet
  (rpenta@redhat.com)
- Unload filtered groups from build config chart (spadgett@redhat.com)
- Fix login tests for OSE variants (sdodson@redhat.com)
- Show build trends chart on build config page (spadgett@redhat.com)
- fix ruby-22 scl enablement (bparees@redhat.com)
- dump build logs on failure (bparees@redhat.com)
- make sure imagestreams are imported before using them with new-app
  (bparees@redhat.com)
- increase build timeout to 60mins (bparees@redhat.com)
- Update config of dind cluster image registry (marun@redhat.com)
- Allow junit output filename to be overridden (marun@redhat.com)
- Optionally skip builds for dev cluster provision (marun@redhat.com)
- Fix for bugz 1283952 and add a test. (smitram@gmail.com)
- Clean up docker-in-docker image (marun@redhat.com)
- Disable delete button for RCs with status replicas (spadgett@redhat.com)
- Web console support for deleting individual builds and deployments
  (spadgett@redhat.com)
- improved os::cmd handling of test names, timing (skuznets@redhat.com)
- UPSTREAM: 14881: fix delta fifo & various fakes for go1.5.1
  (maszulik@redhat.com)
- Update liveness/readiness probe to always use the /healthz endpoint (on the
  stats port or on port 1936 if the stats are disabled). (smitram@gmail.com)
- UPSTREAM: 18065: Fixed forbidden window enforcement in horizontal pod
  autoscaler (sross@redhat.com)
- Fix incorrect status icon on pods page (spadgett@redhat.com)
- Update rest of controllers to use new ProjectsService controller, remove ng-
  controller directives in templates, all controllers defined in routes, minor
  update to tests (admin@benjaminapetersen.me)
- Remove the tooltip from the delete button (spadgett@redhat.com)
- Add success line to dry run (rhcarvalho@gmail.com)
- Add integration test for router healthz endpoint as per @smarterclayton
  review comments. (smitram@gmail.com)
- Improve deployment scaling behavior (ironcladlou@gmail.com)
- UPSTREAM: drop: part of upstream kube PR #15843. (avagarwa@redhat.com)
- UPSTREAM: drop: Fix kube e2e tests in origin. This commit is part of upstream
  kube PR 16360. (avagarwa@redhat.com)
- Bug 1285626 - need to handle IS tag with a from of kind DockerImage
  (jforrest@redhat.com)
- Fix for Bug 1285647 and issue 6025  - Border width will be expanded when long
  value added in Environment Variables for project  - Route link on overview is
  truncated even at wide browser widths (sgoodwin@redhat.com)
- doc: create glusterfs service to persist endpoints (hchen@redhat.com)
- Patch AOS tuned-profiles manpage during build (sdodson@redhat.com)
- Do not print steps for alternative output formats (rhcarvalho@gmail.com)
- UPSTREAM: 17920: Fix frequent kubernetes endpoint updates during cluster
  start (abutcher@redhat.com)
- Add additional route settings to UI (spadgett@redhat.com)
- switch hello-world tests to expect ruby-22 (bparees@redhat.com)
- Upstream: 16728: lengthened pv controller sync period to 10m
  (mturansk@redhat.com)
- Support deleting routes in web console (spadgett@redhat.com)
- oc rsync: pass-thru global command line options (cewong@redhat.com)
- add namespace to field selectors (pweil@redhat.com)
- Use minutes instead of seconds where possible. (vsemushi@redhat.com)
- added volume length check for overriden recycler (mturansk@redhat.com)
- make adding infrastructure SAs easier (deads@redhat.com)
- fixed origin recycler volume config w/ upstream cli flags
  (mturansk@redhat.com)
- oc: Make env use PATCH instead of PUT (mkargaki@redhat.com)
- Prompt before scaling deployments to 0 in UI (spadgett@redhat.com)
- UPSTREAM: 18000: Fix test failure due to days-in-month check. Issue #17998.
  (mkargaki@redhat.com)
- Update install for osdn plugin reorg (danw@redhat.com)
- bump(github.com/openshift/openshift-sdn)
  0d3440e224aeb26a056c0c4c91c30fdbb59588f9 (danw@redhat.com)
- Update various templates to use status-icon (admin@benjaminapetersen.me)
- UPSTREAM: 17973: Validate pod spec.nodeName (jliggitt@redhat.com)
- Rename project service to ProjectsService, update all pre-existing occurances
  (admin@benjaminapetersen.me)
- Hide old deployments in the topology view (spadgett@redhat.com)
- refactored constructors to allow for better code resue with prune-groups
  (skuznets@redhat.com)
- Prevent identical input/output IST in oc new-build (rhcarvalho@gmail.com)
- [RPMs] Add requires on git (sdodson@redhat.com)
- refactored test/cmd/admin to use wrapper functions (skuznets@redhat.com)
- Add aria-describedby attributes to template parameter inputs
  (spadgett@redhat.com)
- remove url workaround (now at correct s2i level) (gmontero@redhat.com)
- New flag to oc new-build to produce no output (rhcarvalho@gmail.com)
- Fix sr-only text for pod status chart (spadgett@redhat.com)
- Add README.md to examples/db-templates (rhcarvalho@gmail.com)
- Fix test registry resource location (ffranz@redhat.com)
- UPSTREAM: 17886: pod log location must validate container if provided
  (ffranz@redhat.com)
- Background the node service so we handle SIGTERM (sdodson@redhat.com)
- hack/util.sh(delete_large_and_empty_logs): optimize find usage.
  (vsemushi@redhat.com)
- Bug 1281928 - fix image stream tagging for DockerImage type images.
  (maszulik@redhat.com)
- Remove type conversion (rhcarvalho@gmail.com)
- Bug1277420 - show friendly prompt when cancelling a completed build
  (jhadvig@redhat.com)
- Add new-build flag to set output image reference (rhcarvalho@gmail.com)
- Output uppercase, hex, 2-character padded serial.txt (jliggitt@redhat.com)
- Fix test/cmd/admin.shwq (jliggitt@redhat.com)
- Fix template processing multiple values (jliggitt@redhat.com)
- CLI usability - proposed aliases (ffranz@redhat.com)
- overhaul imagestream definitions and update latest (bparees@redhat.com)
- refactored test/cmd/images to use wrapper methods (skuznets@redhat.com)
- added unit testing to existing LDAP sync code (skuznets@redhat.com)
- fix macro order for bundled listing in tito custom builder
  (admiller@redhat.com)
- refactor fedora packaging additions with tito custom builder updates
  (admiller@redhat.com)
- Fedora packaging: (admiller@redhat.com)
- added better output to test-end-to-end/core (skuznets@redhat.com)
- refactored scripts to use hack/text (skuznets@redhat.com)
- Typo fixes (jhadvig@redhat.com)
- Update templates to use navigateResourceURL filter where appropriate
  (admin@benjaminapetersen.me)
- Create sourcable bash env as part of dind cluster deploy (marun@redhat.com)
- Update completions (ffranz@redhat.com)
- bump(github.com/spf13/pflag): 08b1a584251b5b62f458943640fc8ebd4d50aaa5
  (ffranz@redhat.com)
- bump(github.com/spf13/cobra): 1c44ec8d3f1552cac48999f9306da23c4d8a288b
  (ffranz@redhat.com)
- Adds .docker/config.json secret example (ffranz@redhat.com)
- refactored test/cmd/basicresources to use wrapper functions
  (skuznets@redhat.com)
- added os::cmd::try_until* (skuznets@redhat.com)
- no redistributable for either fedora or epel (tdawson@redhat.com)
- Fix typo as per review comments from @Miciah (smitram@gmail.com)
- Skip Daemonset and DaemonRestart as these are not enabled yet and keep
  failing. (avagarwa@redhat.com)
- Retry failed attempts to talk to remote registry (miminar@redhat.com)
- Split UI tests into e2e vs rest_api integration suites (jforrest@redhat.com)
- refactored test/cmd/templates to use wrapper methods (skuznets@redhat.com)
- refactored test/cmd/policy to use wrapper methods (skuznets@redhat.com)
- refactored test/cmd/builds to use wrapper methods (skuznets@redhat.com)
- refactored test/cmd/newapp to use wrapper functions (skuznets@redhat.com)
- refactored test/cmd/help to use wrapper functions (skuznets@redhat.com)
- avoid: no such file error in test-cmd (deads@redhat.com)
- added ldap test client and query tests (skuznets@redhat.com)
- Link in the alert for the newly triggered build (jhadvig@redhat.com)
- reorganized ldaputil error and query code (skuznets@redhat.com)
- Fix old PR #4282 code and tests to use new layout (Spec.*) and fix gofmt
  errors. (smitram@gmail.com)
- refactored test/cmd/export to use wrapper functions (skuznets@redhat.com)
- Prohibit passthrough route with path (miciah.masters@gmail.com)
- refactored test/cmd/deployments to use wrapper methods (skuznets@redhat.com)
- refactored test/cmd/volumes to use helper methods (skuznets@redhat.com)
- Update build revision information when building (cewong@redhat.com)
- Enable /healthz irrespective of stats port being enabled/disabled. /healthz
  is available on the stats port or the default stats port 1936 (if stats are
  turned off via --stats-port=0). (smitram@gmail.com)
- refactored test/cmd/secrets to use helper methods (skuznets@redhat.com)
- added cmd util function test to CI (skuznets@redhat.com)
- bump(gopkg.in/asn1-ber.v1): 4e86f4367175e39f69d9358a5f17b4dda270378d
  (jliggitt@redhat.com)
- bump(gopkg.in/ldap.v2): e9a325d64989e2844be629682cb085d2c58eef8d
  (jliggitt@redhat.com)
- Rename github.com/go-ldap/ldap to gopkg.in/ldap.v2 (jliggitt@redhat.com)
- bump(gopkg.in/ldap.v2): b4c9518ccf0d85087c925e4a3c9d5802c9bc7025 (package
  rename) (jliggitt@redhat.com)
- add role reaper (deads@redhat.com)
- Exposes the --token flag in login command help (ffranz@redhat.com)
- allow unknown secret types (deads@redhat.com)
- allow startup of API server only for integration tests (deads@redhat.com)
- bump(github.com/openshift/source-to-image)
  7597eaa168a670767bf2b271035d29b92ab13b5c (cewong@redhat.com)
- refactored hack/test to not use aliases, detect tty (skuznets@redhat.com)
- Refactor pkg/generate/app (rhcarvalho@gmail.com)
- add image-pusher role (deads@redhat.com)
- refactored test-cmd/edit to use new helper methods (skuznets@redhat.com)
- remove db tag from jenkins template (bparees@redhat.com)
- Change default instance size (dmcphers@redhat.com)
- bump the wait for images timeout (bparees@redhat.com)
- dump container logs when s2i incremental tests fail (bparees@redhat.com)
- test non-db sample templates also (bparees@redhat.com)
- Use correct homedir on Windows (ffranz@redhat.com)
- UPSTREAM: 17590: correct homedir on windows (ffranz@redhat.com)
- bump(github.com/openshift/openshift-sdn)
  919e0142fe594ab5115ecf7fa3f7ad4f5810f009 (dcbw@redhat.com)
- Update to new osdn plugin API (dcbw@redhat.com)
- Accept CamelCase versions of TLS config (ccoleman@redhat.com)
- fix git-ls to leverage GIT_SSH for non-git, secret/token access
  (gmontero@redhat.com)
- Bug 1277046 - fixed tagging ImageStreamImage from the same ImageStream to
  point to original pull spec instead of the internal registry.
  (maszulik@redhat.com)
- Get rid of util.StringList (ffranz@redhat.com)
- UPSTREAM: revert: 199adb7: <drop>: add back flag types to reduce noise during
  this rebase (ffranz@redhat.com)
- added start-build parameters to cli.md (ipalade@redhat.com)
- UPSTREAM: 17567: handle the HEAD verb correctly for authorization
  (deads@redhat.com)
- examples/sample-app/README.md: fix commands to simplify user experience.
  (vsemushi@redhat.com)
- Add PostgreSQL replication tests (nagy.martin@gmail.com)
- Allow to override environment and build log level in oc start-build
  (mfojtik@redhat.com)
- Remove hook directory by default in gitserver example (cewong@redhat.com)
- wait for imagestream import before running a build in tests
  (bparees@redhat.com)
- extended tests for docker and sti bc with no outputname defined
  (ipalade@redhat.com)
- The git:// protocol with proxy is not allowed (mfojtik@redhat.com)
- Fix build controller integration test flake (cewong@redhat.com)
- add requester username to project template (deads@redhat.com)
- Fix extended test for start-build (mfojtik@redhat.com)
- prevent go panic when output not specified for build config
  (gmontero@redhat.com)
- fix start-build --from-webhook (cewong@redhat.com)
- SCMAuth: use local proxy when password length exceeds 255 chars
  (cewong@redhat.com)
- Use constants for defaults instead of strings (rhcarvalho@gmail.com)
- Add extended test for proxy (mfojtik@redhat.com)
- Cleanup extended test output some more (nagy.martin@gmail.com)
- Use router's /healtz route for health checks (miminar@redhat.com)
- Unflake MySQL extended test (nagy.martin@gmail.com)
- Add git ls-remote to validate the remote GIT repository (mfojtik@redhat.com)
- Handle openshift.io/build-config.name label as well as buildconfig.
  (vsemushi@redhat.com)
- HACKING.md: clarify meaning and provide proper usage of OUTPUT_COVERAGE
  variable. (vsemushi@redhat.com)
- update the readme (haoran@dhcp-129-204.nay.redhat.com)
- Completions for persistent flags (ffranz@redhat.com)
- UPSTREAM: spf13/cobra 180: fixes persistent flags completions
  (ffranz@redhat.com)
- Generated docs must use the short command name (ffranz@redhat.com)
- UPSTREAM: 17033: Fix default value for StreamingConnectionIdleTimeout
  (avagarwa@redhat.com)
- Fixes bug 1275518 https://bugzilla.redhat.com/show_bug.cgi?id=1275518
  (avagarwa@redhat.com)
- tito builder/tagger cleanup: (admiller@redhat.com)
- stop oc export from exporting SA secrets that aren't round-trippable
  (deads@redhat.com)
- accept new dockercfg format (deads@redhat.com)
- Fix alignment of icon on settings page by overriding patternfly rule
  (sgoodwin@redhat.com)
- spec: Use relative symlinks in bin/ (walters@verbum.org)
- Added readiness probe for Router (miminar@redhat.com)
- Add openshift/origin-gitserver to push-release.sh (cewong@redhat.com)
- To replace Func postfixed identifier with Fn postfixed in e2e extended
  (salvatore-dario.minonne@amadeus.com)
- to add a job test to extended test (salvatore-dario.minonne@amadeus.com)
- Allow kubelet to be configured for dind compat (marun@redhat.com)
- Force network tests to wait until cluster is ready (marun@redhat.com)
- Update dind docs to configure more vagrant memory (marun@redhat.com)
- Run networking sanity checks separately. (marun@redhat.com)
- Add 'redeploy' command to dind cluster script (marun@redhat.com)
- Fix networking extended test suite declaration (marun@redhat.com)
- Skip internet check in network extended test suite (marun@redhat.com)
- Skip sdn node during dev cluster deploy (marun@redhat.com)
- Fix handling of network plugin arg in deployment (marun@redhat.com)
- Ensure deltarpm is used for devcluster deployment. (marun@redhat.com)
- Rename OPENSHIFT_SDN env var (marun@redhat.com)
- Refactor extended networking test script (marun@redhat.com)
- Increase verbosity of networking test setup (marun@redhat.com)
- Deploy ssh by default on dind cluster nodes (marun@redhat.com)
- Fix numeric comparison bug in cluster provisioning (marun@redhat.com)
- Make provisioning output less noisy (marun@redhat.com)
- Retain systemd logs from extended networking tests (marun@redhat.com)
- Allow networking tests to target existing cluster (marun@redhat.com)
- Optionally skip builds during cluster provision (marun@redhat.com)
- Enable parallel dev cluster deployment (marun@redhat.com)
- Disable scheduling for sdn node when provisioning (marun@redhat.com)
- Rename bash functions used for provisioning (marun@redhat.com)
- Doc and env var cleanup for dind refactor (marun@redhat.com)
- Switch docker-in-docker to use systemd (marun@redhat.com)
- fix merge conflicts in filters/resources.js, update bindata
  (gabriel_ruiz@symantec.com)
- add tests for variable expansion (bparees@redhat.com)
- Use assets/config.local.js if present for development config
  (spadgett@redhat.com)
- Fix typos (dmcphers@redhat.com)
- Allow tag already exist when pushing a release (ccoleman@redhat.com)
- Fixes attach example (ffranz@redhat.com)
- UPSTREAM: 17239: debug filepath in config loader (ffranz@redhat.com)
- Allow setting build config environment variables, show env vars on build
  config page (jforrest@redhat.com)
- UPSTREAM: 17236: fixes attach example (ffranz@redhat.com)
- Remove failing Docker Registry client test (ccoleman@redhat.com)
- leverage new source-to-image API around git clone spec validation/correction
  (gmontero@redhat.com)
- Reload proxy rules on firewalld restart, etc (danw@redhat.com)
- Don't say "will retry in 5s seconds" in push failure message
  (danw@redhat.com)
- Fix serviceaccount in gitserver example yaml (cewong@redhat.com)
- gitserver: return appropriate error when auth fails (cewong@redhat.com)
- provide validation for build source type (bparees@redhat.com)
- Show less output in test-cmd.sh (ccoleman@redhat.com)
- Change the image workdir to be /var/lib/origin (ccoleman@redhat.com)
- bump(github.com/openshift/source-to-image):
  c9985b5443c4a0a0ffb38b3478031dcc2dc8638d (gmontero@redhat.com)
- Add deployment logs to UI (spadgett@redhat.com)
- Push recycler image (jliggitt@redhat.com)
- Prevent sending username containing colon via basic auth
  (jliggitt@redhat.com)
- added test-cmd test wrapper functions and tests (skuznets@redhat.com)
- Dont loop over all the builds / deployments for the config when we get an
  update for one (jforrest@redhat.com)
- Avoid mobile Safari zoom on input focus (spadgett@redhat.com)
- add build pod name annotation to builds (bparees@redhat.com)
- Prevent autocorrect and autocapitilization for some inputs
  (spadgett@redhat.com)
- bump rails test retry timeout (bparees@redhat.com)
- Adding the recycle tool to the specfile (bleanhar@redhat.com)
- Prevent route from overflowing box in mobile Safari (spadgett@redhat.com)
- Update recycler image to use binary (jliggitt@redhat.com)
- bump(go-ldap/ldap): b4c9518ccf0d85087c925e4a3c9d5802c9bc7025
  (skuznets@redhat.com)
- status: Warn about transient deployment trigger errors (mkargaki@redhat.com)
- Updated pv recycler to work with uid:gid (mturansk@redhat.com)
- Set registry service's session affinity (miminar@redhat.com)
- Several auto-completion fixes (ffranz@redhat.com)
- Fixes auto-completion for build config names (ffranz@redhat.com)
- show warning when pod's containers are restarting (deads@redhat.com)
- Change how we store association between builds and ICTs on DCs for the
  console overview (jforrest@redhat.com)
- eliminate double bc reporting in status (deads@redhat.com)
- Use a different donut color for pods not ready (spadgett@redhat.com)
- change OS bootstrap SCCs to use RunAsAny for fsgroup and sup groups
  (pweil@redhat.com)
- UPSTREAM:<carry>:v1beta3 default fsgroup/supgroup strategies to RunAsAny
  (pweil@redhat.com)
- UPSTREAM:<carry>:default fsgroup/supgroup strategies to RunAsAny
  (pweil@redhat.com)
- disable --validate flag by default (deads@redhat.com)
- Update CONTRIBUTING.adoc (bpeterse@redhat.com)
- UPSTREAM: 17061: Unnecessary updates to ResourceQuota when doing UPDATE
  (decarr@redhat.com)
- Show deployment status on overview when failed or cancelled
  (spadgett@redhat.com)
- UPSTREAM: revert: 0048df4: <carry>: Disable --validate by default
  (deads@redhat.com)
- add reconcile-cluster-role arg for specifying specific roles
  (deads@redhat.com)
- Reduce number of tick labels in metrics sparkline (spadgett@redhat.com)
- fix openshift client cache for different versions (deads@redhat.com)
- UPSTREAM: 17058: fix client cache for different versions (deads@redhat.com)
- Fix typo (dmcphers@redhat.com)
- make export-all work in failures (deads@redhat.com)
- Fix build-waiting logic to use polling instead of watcher
  (nagy.martin@gmail.com)
- Update HPA bootstrap policy (sross@redhat.com)
- add APIGroup to role describer (deads@redhat.com)
- UPSTREAM: 17017: stop jsonpath panicing on bad array length
  (deads@redhat.com)
- don't update the build phase once it reaches a terminal state
  (bparees@redhat.com)
- Run deployer as non-root user (ironcladlou@gmail.com)
- Run registry as non-root user (ironcladlou@gmail.com)
- warn on missing log and metric URLs for console (deads@redhat.com)
- don't show context nicknames that users don't recognize (deads@redhat.com)
- Allow non-alphabetic characters in expression generator (mfojtik@redhat.com)
- Add jenkins status to readme (dmcphers@redhat.com)
- cAdvisor needs access to dmsetup for devicemapper info (ccoleman@redhat.com)
- WIP - try out upstream e2e (ccoleman@redhat.com)
- Make auth-in-container tests cause test failure again (ccoleman@redhat.com)
- UPSTREAM: 16969: nsenter file writer mangles newlines (ccoleman@redhat.com)
- Doc fixes (mkargaki@redhat.com)
- Doc fixes (dmcphers@redhat.com)
- Specify scheme/port for metrics client (jliggitt@redhat.com)
- UPSTREAM: 16926: Enable specifying scheme/port for metrics client
  (jliggitt@redhat.com)
- Test template preservation of integers (jliggitt@redhat.com)
- UPSTREAM: 16964: Preserve int64 data when unmarshaling (jliggitt@redhat.com)
- Given we don't restrict on Travis success.  Make what it does report be 100%%
  reliable and fast.  So when it does fail we know something is truly wrong.
  (dmcphers@redhat.com)
- add a wordpress template (bparees@redhat.com)
- bump(github.com/openshift/openshift-sdn)
  d5965ee039bb85c5ec9ef7f455a8c03ac0ff0214 (dcbw@redhat.com)
- Identify the upstream Kube tag more clearly (ccoleman@redhat.com)
- UPSTREAM: 16945: kubelet: Fallback to api server for pod status
  (mkargaki@redhat.com)
- Allow in-cluster config for oc (ccoleman@redhat.com)
- Move etcd.log out of etcd dir (jliggitt@redhat.com)
- Conditionally run extensions controllers (jliggitt@redhat.com)
- deprecation for buildconfig label (bparees@redhat.com)
- Unable to submit subject rolebindings to a v1 server (ccoleman@redhat.com)
- Allow a service account installation (ccoleman@redhat.com)
- back project cache with local authorizer (deads@redhat.com)
- Make namespace delete trigger exp resource delete (sross@redhat.com)
- UPSTREAM: 15537: openstack: cache InstanceID and use it for volume
  management. (jsafrane@redhat.com)
- Bug 1278007 - Use commit instead of HEAD when streaming in start-build
  (mfojtik@redhat.com)
- Move os::util:install-sdn to contrib/node/install-sdn.sh (sdodson@redhat.com)
- Drop selinux relabeling for volumes, add images to push-release
  (sdodson@redhat.com)
- UPSTREAM: 16818: Namespace controller should always get latest state prior to
  deletion (decarr@redhat.com)
- UPSTREAM: 16859: Return a typed error for no-config (ccoleman@redhat.com)
- Build controller - set build status only if pod creation succeeds
  (cewong@redhat.com)
- New-app: Set context directory and strategy on source repos specified with
  tilde(~) (cewong@redhat.com)
- Let users to select log content without line numbers (spadgett@redhat.com)
- pre-set the SA namespaces (deads@redhat.com)
- Add labels and annotations to DeploymentStrategy. (roque@juniper.net)
- update UPGRADE.md (pweil@redhat.com)
- add reconcile-sccs command (pweil@redhat.com)
- containerized-installs -> containerized (sdodson@redhat.com)
- Add example systemd units for running as container (sdodson@redhat.com)
- Add sdn ovs enabled node image (sdodson@redhat.com)
- Guard against servers that return non-json for the /v2/ check
  (ccoleman@redhat.com)
- Added PVController service account (mturansk@redhat.com)
- Disable deployment config detail message updates (ironcladlou@gmail.com)
- updates via github discussions (admin@benjaminapetersen.me)
- UPSTREAM: 16432: fixed pv binder race condition (mturansk@redhat.com)
- Fixes completions (ffranz@redhat.com)
- UPSTREAM: spf13/cobra: fixes filename completion (ffranz@redhat.com)
- Revert 7fc8ab5b2696b533e6ac5bea003e5a0622bdbf58 (jordan@liggitt.net)
- fix case for events (deads@redhat.com)
- UPSTREAM: 16384: Large memory allocation with key prefix generation
  (ccoleman@redhat.com)
- Update bash completions (decarr@redhat.com)
- UPSTREAM: 16749: Kubelet serialize image pulls had incorrect default
  (decarr@redhat.com)
- UPSTREAM: 15914: make kubelet images pulls serialized by default
  (decarr@redhat.com)
- prune: Remove deployer pods when pruning failed deployments
  (mkargaki@redhat.com)
- New kibanna archive log link on log tab for build & pod
  (admin@benjaminapetersen.me)
- Transfer ImagePullSecrets to deployment hook pods (ironcladlou@gmail.com)
- Copy volume mounts to hook pods (ironcladlou@gmail.com)
- UPSTREAM: 16717: Ensure HPA has valid resource/name/subresource, validate
  path segments (jliggitt@redhat.com)
- Switch back to subnet (dmcphers@redhat.com)
- Inline deployer hook logs (ironcladlou@gmail.com)
- Remove default subnet (dmcphers@redhat.com)
- Disable quay.io test (ccoleman@redhat.com)
- UPSTREAM: 16032: revert origin 03e50db: check if /sbin/mount.nfs is present
  (mturansk@redhat.com)
- UPSTREAM: 16277: Fixed resetting last scale time in HPA status
  (sross@redhat.com)
- Change subnet default (dmcphers@redhat.com)
- Add default subnet back (dmcphers@redhat.com)
- Remove default subnet (dmcphers@redhat.com)
- bump(github.com/openshift/openshift-sdn)
  cb0e352cd7591ace30d592d4f82685d2bcd38a04 (rpenta@redhat.com)
- Disable new-app Git tests in Vagrant (ccoleman@redhat.com)
- oc logs long description is wrong (ffranz@redhat.com)
- scc sort by priority (pweil@redhat.com)
- UPSTREAM:<carry>:v1beta3 scc priority field (pweil@redhat.com)
- UPSTREAM:<carry>:scc priority field (pweil@redhat.com)
- Bug and issue fixes (3) (sgoodwin@redhat.com)
- Fix deploy test conflict flake (ironcladlou@gmail.com)
- Prevent early exit on install-assets failure (jliggitt@redhat.com)
- UPSTREAM: 15997: Prevent NPE in resource printer on HPA (ccoleman@redhat.com)
- UPSTREAM: 16478: Daemon controller shouldn't place pods on not ready nodes
  (ccoleman@redhat.com)
- UPSTREAM: 16340: Kubelet pod status update is not correctly occuring
  (ccoleman@redhat.com)
- UPSTREAM: 16191: Mirror pods don't show logs (ccoleman@redhat.com)
- UPSTREAM: 14182: Distinguish image registry unavailable and pull failure
  (decarr@redhat.com)
- UPSTREAM: 16174: NPE when checking for mounting /etc/hosts
  (ccoleman@redhat.com)
-  Bug 1275537 - Fixed the way image import controller informs about errors
  from imports. (maszulik@redhat.com)
- UPSTREAM: 16052: Control /etc/hosts in the kubelet (ccoleman@redhat.com)
- UPSTREAM: 16044: Don't shadow error in cache.Store (ccoleman@redhat.com)
- UPSTREAM: 16025: Fix NPE in describe of HPA (ccoleman@redhat.com)
- UPSTREAM: 16668: Fix hpa escalation (deads@redhat.com)
- UPSTREAM: 15944: DaemonSet controller modifies the wrong fields
  (ccoleman@redhat.com)
- UPSTREAM: 15414: Annotations for kube-proxy move to beta
  (ccoleman@redhat.com)
- UPSTREAM: 15745: Endpoint timeouts in the proxy are bad (ccoleman@redhat.com)
- UPSTREAM: 15646: DaemonSet validation (ccoleman@redhat.com)
- UPSTREAM: 15574: Validation on resource quota (ccoleman@redhat.com)
- fix contrib doc (pweil@redhat.com)
- Calculate correct bottom scroll position (spadgett@redhat.com)
- oc tag should retry on conflict errors (ccoleman@redhat.com)
- Remove log arg for travis (jliggitt@redhat.com)
- hack/install-assets: fix nonstandard bash (lmeyer@redhat.com)
- extend role covers with groups (deads@redhat.com)
- Bug 1277021 - Fixed import-image help information. (maszulik@redhat.com)
- Deprecate build-logs in favor of logs (mkargaki@redhat.com)
- Build and deployment logs should check kubelet response (ccoleman@redhat.com)
- DNS services are not resolving properly (ccoleman@redhat.com)
- hack/test-end-to-end.sh won't start on IPv6 system (ccoleman@redhat.com)
- Wait longer for etcd startup in integration tests (ccoleman@redhat.com)
- Restore detailed checking for forbidden exec (jliggitt@redhat.com)
- UPSTREAM: 16711: Read error from failed upgrade attempts
  (jliggitt@redhat.com)
- Only show scroll links when log is offscreen (spadgett@redhat.com)
- Temporarily accept 'Forbidden' and 'forbidden' responses
  (jliggitt@redhat.com)
- Add HPA support for DeploymentConfig (sross@redhat.com)
- UPSTREAM: 16570: Fix GetRequestInfo subresource parsing for proxy/redirect
  verbs (sross@redhat.com)
- UPSTREAM: 16671: Customize HPA Heapster service namespace/name
  (sross@redhat.com)
- Add Scale Subresource to DeploymentConfigs (sross@redhat.com)
- bz 1276319 - Fix oc rsync deletion with tar strategy (cewong@redhat.com)
- UPSTREAM: <carry>: s/imagestraams/imagestreams/ in `oc get`
  (eparis@redhat.com)
- UPSTREAM(go-dockerclient): 408: fix stdin-only attach (agoldste@redhat.com)
- Add error clause to service/project.js (admin@benjaminapetersen.me)
- Switch to checking for CrashLoopBackOff to show the container looping message
  (jforrest@redhat.com)
- Fix namespace initialization (jliggitt@redhat.com)
- UPSTREAM: 16590: Create all streams before copying in exec/attach
  (agoldste@redhat.com)
- UPSTREAM: 16677: Add Validator for Scale Objects (sross@redhat.com)
- UPSTREAM: 16537: attach must only allow a tty when container supports it
  (ffranz@redhat.com)
- Bug 1276602 - fixes error when scaling dc with --timeout (ffranz@redhat.com)
- test/cmd/admin.sh isn't reentrant (ccoleman@redhat.com)
- add group/version serialization to master (deads@redhat.com)
- UPSTREAM: <drop>: allow specific, skewed group/versions (deads@redhat.com)
- UPSTREAM: 16667: Make Kubernetes HPA Controller use Namespacers
  (sross@redhat.com)
- rsync: output warnings to stdout instead of using glog (cewong@redhat.com)
- Throttle log updates to avoid UI flicker (spadgett@redhat.com)
- allow cluster-admin and cluster-reader to use different groups
  (deads@redhat.com)
- UPSTREAM: 16127: Bump cAdvisor (jimmidyson@gmail.com)
- UPSTREAM: 15612: Bump cadvisor (jimmidyson@gmail.com)
- Bug 1277017 - Added checking if spec.DockerImageRepository and spec.Tags are
  not empty. (maszulik@redhat.com)
- rsync: output warnings to stdout instead of using glog (cewong@redhat.com)
- Bug 1276657 - Reuse --insecure-registry flag value when creating ImageStream
  from passed docker image. (maszulik@redhat.com)
- Use pficon-info on pod terminal tab (spadgett@redhat.com)
- Bug 1268000 - replace Image.DockerImageReference with value from status.
  (maszulik@redhat.com)
- reenable static building of hello pod (bparees@redhat.com)
- Add and test field label conversions (jliggitt@redhat.com)
- logs: View logs from older deployments/builds with --version
  (mkargaki@redhat.com)
- UPSTREAM: 15733: Disable keepalive on liveness probes (ccoleman@redhat.com)
- UPSTREAM: 15845: Add service locator in service rest storage
  (ccoleman@redhat.com)
- UPSTREAM: 16223: Concurrency fixes in kubelet status manager
  (ccoleman@redhat.com)
- UPSTREAM: 15275: Kubelet reacts much faster to unhealthy containers
  (ccoleman@redhat.com)
- install-assets: retry bower update (lmeyer@redhat.com)
- bump(github.com/openshift/openshift-sdn)
  1f449c7f0d3cd41314a895ef119f9d25a15b54de (rpenta@redhat.com)
- UPSTREAM: 16033: Mount returns verbose error (ccoleman@redhat.com)
- UPSTREAM: 16032: check if /sbin/mount.nfs is present (ccoleman@redhat.com)
- Improve UI performance when displaying large logs (spadgett@redhat.com)
- UPSTREAM: 15555: Use default port 3260 for iSCSI (ccoleman@redhat.com)
- UPSTREAM: 15562: iSCSI use global path to mount (ccoleman@redhat.com)
- fixes as per @smarterclayton review comments. (smitram@gmail.com)
- UPSTREAM: 15236: Better error output from gluster (ccoleman@redhat.com)
- new SCCs (pweil@redhat.com)
- UPSTREAM: 16068: Increase annotation size significantly (ccoleman@redhat.com)
- UPSTREAM(go-dockerclient): 408: fix stdin-only attach (agoldste@redhat.com)
- stop creating roles with resourcegroups (deads@redhat.com)
- Fixes as per @smarterclayton and @liggit review comments. (smitram@gmail.com)
- UPSTREAM: 15706: HorizontalPodAutoscaler and Scale subresource APIs graduated
  to beta (sross@redhat.com)
- Fixed how tags are being printed when describing ImageStream. Previously the
  image.Spec.Tags was ignored, which resulted in not showing the tags for which
  there were errors during imports. (maszulik@redhat.com)
- Various style/positioning fixes (sgoodwin@redhat.com)
- Add missing kube resources to bootstrap policy (jliggitt@redhat.com)
- UPSTREAM: <carry>: OpenShift 3.0.2 nodes report v1.1.0-alpha
  (ccoleman@redhat.com)
- UPSTREAM: 16137: Release node port correctly (ccoleman@redhat.com)
- Run serialization tests for upstream types (mkargaki@redhat.com)
- UPSTREAM: <carry>: Update v1beta3 (mkargaki@redhat.com)
- UPSTREAM: 15930: Deletion of pods managed by old kubelets
  (ccoleman@redhat.com)
- UPSTREAM: 15900: Delete succeeded and failed pods immediately
  (ccoleman@redhat.com)
- add istag list, update (deads@redhat.com)
- diagnostics: default server conf paths changed (lmeyer@redhat.com)
- diagnostics: systemd unit name changes (lmeyer@redhat.com)
- Handle passwords with colon in basic auth (pep@redhat.com)
- UPSTREAM: 15961: Add streaming subprotocol negotation (agoldste@redhat.com)
- Systemd throws an error on Restart=Always (sdodson@redhat.com)
- Bug 1275564 - Removed the requirement for spec.dockerImageRepository from
  import-image command. (maszulik@redhat.com)
- bump(github.com/openshift/source-to-image)
  65d46436ab599633b76e570311a05f46a818389b (mfojtik@redhat.com)
- Add openshift.io/build-config.name label to builds. (vsemushi@redhat.com)
- oc: Use default resources where it makes sense (mkargaki@redhat.com)
- logs: Support all flags for builds and deployments (mkargaki@redhat.com)
- UPSTREAM: <carry>: Update v1beta3 PodLogOptions (mkargaki@redhat.com)
- UPSTREAM: 16494: Remove dead pods upon stopping a job (maszulik@redhat.com)
- Add local IP addresses to node certificate (jliggitt@redhat.com)
- Rest validation of binary builds is more aggressive (ccoleman@redhat.com)
-   o Add support to expose/redirect/disable insecure schemes (http) for
  edge secured routes.   o Add changes to template, haproxy and f5 router
  implementations.   o Add generated* files. (smitram@gmail.com)
- removed unneeded squash and chown from nfs doc (mturansk@redhat.com)
- Only run pod nodeenv admission on create (agoldste@redhat.com)
- fix up latest tags and add new scl image versions (bparees@redhat.com)
- UPSTREAM: 16532: Allow log tail and log follow to be specified together
  (ccoleman@redhat.com)
- Need to be doing a bower update instead of install so dependencies will
  update without conflict (jforrest@redhat.com)
- Update swagger spec (pmorie@gmail.com)
- UPSTREAM: 15799: Fix PodPhase issue caused by backoff (mkargaki@redhat.com)
- watchObject in console triggers callbacks for events of items of the same
  kind (jforrest@redhat.com)
- status: Report routes that have no route port specified (mkargaki@redhat.com)
- Add special casing for v1beta3 DeploymentConfig in serialization_test
  (pmorie@gmail.com)
- UPSTREAM: <carry>: respect fuzzing defaults for v1beta3 SecurityContext
  (pmorie@gmail.com)
- OS integration for PSC (pweil@redhat.com)
- UPSTREAM: <carry>: v1beta3 scc integration for PSC (pweil@redhat.com)
- UPSTREAM: <carry>: scc integration for PSC (pweil@redhat.com)
- UPSTREAM: <carry>: Workaround for cadvisor/libcontainer config schema
  mismatch (pmorie@gmail.com)
- UPSTREAM: 15323: Support volume relabling for pods which specify an SELinux
  label (pmorie@gmail.com)
- Update completions (jimmidyson@gmail.com)
- Test scm password auth (jliggitt@redhat.com)
- Add prometheus exporter to haproxy router (jimmidyson@gmail.com)
- UPSTREAM: 16332: Remove invalid blank line when printing jobs
  (maszulik@redhat.com)
- UPSTREAM: 16234: Fix jobs unittest flakes (maszulik@redhat.com)
- UPSTREAM: 16196: Fix e2e test flakes (maszulik@redhat.com)
- UPSTREAM: 15791: Update master service ports and type via controller.
  (abutcher@redhat.com)
- Add dns ports to the master service (abutcher@redhat.com)
- UPSTREAM: 15352: FSGroup implementation (pmorie@gmail.com)
- UPSTREAM: 14705: Inline some SecurityContext fields into PodSecurityContext
  (pmorie@gmail.com)
- UPSTREAM: 14991: Add Support for supplemental groups (pmorie@gmail.com)
- Allow processing template from different namespace (mfojtik@redhat.com)
- changed build for sti and docker to use OutputDockerImageReference, fixed
  tests (ipalade@redhat.com)
- Provide informational output in new-app and new-build (ccoleman@redhat.com)
- Bug 1270728 - username in the secret don't override the username in the
  source URL (jhadvig@redhat.com)
- UPSTREAM: 15520: Move job to generalized label selector (maszulik@redhat.com)
- Revert 'Retry ISM save upon conflicting IS error' commit upon retry mechanism
  introduced in ISM create method (maszulik@redhat.com)
- Bug 1275003: expose: Set route port based on service target port
  (mkargaki@redhat.com)
- Improve generation of name based on a git repo url to make it valid.
  (vsemushi@redhat.com)
- UPSTREAM: 16080: Convert from old mirror pods (1.0 to 1.1)
  (ccoleman@redhat.com)
- UPSTREAM: 15983: Store mirror pod hash in annotation (ccoleman@redhat.com)
- Slightly better output order in the CLI for login (ccoleman@redhat.com)
- Attempt to find merged parent (ccoleman@redhat.com)
- Fix extended tests for --from-* binary (ccoleman@redhat.com)
- Completions (ffranz@redhat.com)
- UPSTREAM: 16482: stdin is not a file extension for bash completions
  (ffranz@redhat.com)
- Bump angular-pattern to version 2.3.4 (spadgett@redhat.com)
- Use cmdutil.PrintSuccess to print objects (ffranz@redhat.com)
- Improve the error messages when something isn't found (ccoleman@redhat.com)
- UPSTREAM: 16445: Capitalize and expand UsageError message
  (ccoleman@redhat.com)
- Updates to address several issues (sgoodwin@redhat.com)
- Refactor to use ExponentialBackoff (ironcladlou@gmail.com)
- bump(github.com/openshift/openshift-sdn)
  c08ebda0774795eec624b5ce9063662b19959cf3 (rpenta@redhat.com)
- Auto-generated docs/bash-completions for 'oadm pod-network make-projects-
  global' (rpenta@redhat.com)
- Show empty deployments on overview if latest (spadgett@redhat.com)
- Support retrying mapping creation on conflict (ironcladlou@gmail.com)
- Support installation via containers in new-app (ccoleman@redhat.com)
- Disable create form inputs and submit button while the API request is
  happening (jforrest@redhat.com)
- fix project request with quota (deads@redhat.com)
- UPSTREAM: 16441: Pass runtime.Object to Helper.Create/Replace
  (deads@redhat.com)
- Update openshift-object-describer to 1.1.1 (jforrest@redhat.com)
- Slim down the extended tests (ccoleman@redhat.com)
- upper case first letter of status message (bparees@redhat.com)
- Rsync fixes (cewong@redhat.com)
- better error message for missing dockerfile (bparees@redhat.com)
- add verbose logging to new-app flake and remove extraneous tryuntil logging
  (bparees@redhat.com)
- Support --binary on new-build (ccoleman@redhat.com)
- Fix text-overflow issue on Safari (sgoodwin@redhat.com)
- bump(github.com/openshift/source-to-image)
  9728b53c11218598acb2cc1b9c8cc762c36f44bc (cewong@redhat.com)
- Include name of port in pod template, switch to port/protocol format
  (jforrest@redhat.com)
- Various logs fixes: (admin@benjaminapetersen.me)
- add --context-dir flag to new-build (bparees@redhat.com)
- bump(github.com/openshift/openshift-sdn)
  22b9a4176435ac4453c30c53799338979ef79050 (rpenta@redhat.com)
- Adding border above builds without a service so that they look more
  connected. (sgoodwin@redhat.com)
- Updates to the log-view so that it's more inline with pod terminal. And
  switch to more subtle ellipsis loader. (sgoodwin@redhat.com)
- Expose all container ports creating from source in the UI
  (spadgett@redhat.com)
- Fail if timeout is reached (ccoleman@redhat.com)
- UPSTREAM: 15975: Validate names in BeforeCreate (jliggitt@redhat.com)
- Bug 1275234 - fixes --resource-version error in scale (ffranz@redhat.com)
- skip project validation when creating a new-project (deads@redhat.com)
- Show route target port in the routes table if its set (jforrest@redhat.com)
- Allow users to click monopod donut charts on overview (spadgett@redhat.com)
- Add verbose output to test execution (marun@redhat.com)
- Show warning popup when builds have a status message (jforrest@redhat.com)
- UPSTREAM: 16241: Deflake wsstream stream_test.go (ccoleman@redhat.com)
- do not make redistributable in fedora (tdawson@redhat.com)
- Make building clients for other architectures optional (tdawson@redhat.com)
- Read kubernetes remote from git repository. (maszulik@redhat.com)
- Fix dind vagrant provisioning and test execution (marun@redhat.com)
- Bug 1261548 - oc run --attach support for DeploymentConfig
  (ffranz@redhat.com)
- Use server time for end time in metrics requests (spadgett@redhat.com)
- Fix typo (jliggitt@redhat.com)
- Update angular-patternfly to version 2.3.3 (spadgett@redhat.com)
- UPSTREAM: 16109: expose attachable pod discovery in factory
  (ffranz@redhat.com)
- libvirt use nfs for dev cluster synced folder (marun@redhat.com)
- report a warning and do not continue on a partial match (bparees@redhat.com)
- Move the cgroup regex to package level. (roque@juniper.net)
- UPSTREAM: 16286: Avoid CPU hotloop on client-closed websocket
  (jliggitt@redhat.com)
- Increase vagrant memory default by 512mb (marun@redhat.com)
- Source dind script from the docker repo (marun@redhat.com)
- dind: Fix disabling of sdn node scheduling (marun@redhat.com)
- Switch dind image to use fedora 21 (marun@redhat.com)
- Only run provision-full.sh for single-vm clusters (marun@redhat.com)
- Fix extended network test invocation (marun@redhat.com)
- Invoke docker with sudo when archiving test logs (marun@redhat.com)
- Enhance dind vagrant deployment (marun@redhat.com)
- Add dind detail to the contribution doc (marun@redhat.com)
- Enhance dind-cluster.sh documentation (marun@redhat.com)
- bump(github.com/openshift/openshift-sdn):
  1e4edc9abb6bb8ac7e5cd946ddec4c10cc714d67 (danw@redhat.com)
- Add rsync daemon copy strategy for windows support (cewong@redhat.com)
- UPSTREAM: 11694: http proxy support for exec/pf (agoldste@redhat.com)
- hack/cherry-pick.sh: fix typo (agoldste@redhat.com)
- hack/cherry-pick.sh: support binary files in diffs (agoldste@redhat.com)
- Added job policy (maszulik@redhat.com)
- platformmanagement_public_514 - Allow importing tags from ImageStreams
  pointing to external registries. (maszulik@redhat.com)
- Minor fix for nfs readme (liangxia@users.noreply.github.com)
- delete: Remove both image stream spec and status tags (mkargaki@redhat.com)
- move newapp commands that need docker into extended tests
  (bparees@redhat.com)
- Only watch pod statuses for overview donut chart (spadgett@redhat.com)
- Vagrantfile should allow multiple sync folders (ccoleman@redhat.com)
- Fix context dir for STI (ccoleman@redhat.com)
- Fixing typos (dmcphers@redhat.com)
- Deflake test/cmd/newapp.sh (ccoleman@redhat.com)
- Review comments (ccoleman@redhat.com)
- Docs (ccoleman@redhat.com)
- Completions (ccoleman@redhat.com)
- Generated conversions (ccoleman@redhat.com)
- Docker and STI builder images support binary extraction (ccoleman@redhat.com)
- Enable binary build endpoint and CLI via start-build (ccoleman@redhat.com)
- UPSTREAM: 15053<carry>: Conversions for v1beta3 (ccoleman@redhat.com)
- UPSTREAM: 15053: Support stdinOnce and fix attach (ccoleman@redhat.com)
- Disable all e2e portforward tests (ccoleman@redhat.com)
- Fixes infinite loop on login and forces auth when password were provided
  (ffranz@redhat.com)
- increase timeout for helper pods (bparees@redhat.com)
- bump(github.com/openshift/source-to-image)
  84e4633329181926ec8d746e189769522b1ff6a7 (roque@juniper.net)
- More cleanup of the individual pages, use the extra space better
  (jforrest@redhat.com)
- When running as a pod, pass the network context to source-to-image.
  (roque@juniper.net)
- allow dockersearcher to be setup after config is parsed (bparees@redhat.com)
- UPSTREAM: <carry>: Back n forth downward/metadata conversions
  (maszulik@redhat.com)
- Ensure no overlap between SDN cluster network and service/portal network
  (rpenta@redhat.com)
- don't attempt to call create on files that don't exist (bparees@redhat.com)
- Use remove() rather than html('') to empty SVG element (spadgett@redhat.com)
- enable storage interface functions (deads@redhat.com)
- Retry ISM save upon conflicting IS error (maszulik@redhat.com)
- [RPMS] expand obsoletes to include OSE versions (sdodson@redhat.com)
- [RPMS] bump docker requirement to 1.8.2 (sdodson@redhat.com)
- assets: Update topology-graph widget (stefw@redhat.com)
- logs: Re-use from upstream (mkargaki@redhat.com)
- assets: Use $evalAsync when updating topology widget (stefw@redhat.com)
- Handle data gaps when calculating CPU usage in UI (spadgett@redhat.com)
- add SA and role for job and hpa controllers (deads@redhat.com)
- UPSTREAM: 16067: Provide a RetryOnConflict helper for client libraries
  (maszulik@redhat.com)
- UPSTREAM: 10707: logs: Use resource builder (mkargaki@redhat.com)
- Update pod status chart styles (spadgett@redhat.com)
- rework how allow-missing-images resolves (bparees@redhat.com)
- bump(github.com/docker/spdystream): 43bffc4 (agoldste@redhat.com)
- Remove unused godep (agoldste@redhat.com)
- Increase height of metrics utilization sparkline (spadgett@redhat.com)
- Disable a known broken test (ccoleman@redhat.com)
- UID repair should not fail when out of range allocation (ccoleman@redhat.com)
- Add v1beta3 removal notes to UPGRADE.md (ironcladlou@gmail.com)
- Add iptables to origin image (sdodson@redhat.com)
- policy changes for extensions (deads@redhat.com)
- enable extensions (deads@redhat.com)
- UPSTREAM: 15194: Avoid spurious "Hairpin setup failed..." errors
  (danw@gnome.org)
- UPSTREAM: 7f6f85bd7b47db239868bcd868ae3472373a4f05: fixes attach broken
  during the refactor (ffranz@redhat.com)
- UPSTREAM: 16042: fix missing error handling (deads@redhat.com)
- UPSTREAM: 16084: Use NewFramework in all tests (ccoleman@redhat.com)
- e2e: Verify service account token and log cli errors (ccoleman@redhat.com)
- add commands for managing SCCs (deads@redhat.com)
- Allow patching events (jliggitt@redhat.com)
- Fix problems with overview donut chart on IE (spadgett@redhat.com)
- Bug 1274200: Prompt by default when deleting a non-existent tag
  (mkargaki@redhat.com)
- correct htpasswd error handling: (deads@redhat.com)
- Set build.status.reason on error (rhcarvalho@gmail.com)
- Fixes several issues with tabbed output (ffranz@redhat.com)
- Referenced tags should get updated on a direct tag (ccoleman@redhat.com)
- oc tag should take an explicit reference to ImageStreamImage
  (ccoleman@redhat.com)
- Add back a fix for the libvirt dev_cluster case (danw@redhat.com)
- Completions (ccoleman@redhat.com)
- Fixes 'oc edit' file blocking on windows (ffranz@redhat.com)
- On Windows, use CRLF line endings in oc edit (ccoleman@redhat.com)
- Add iptables requirement to openshift package (sdodson@redhat.com)
- Remove extra copy of main.css from bindata (jforrest@redhat.com)
- add grace period for evacuate (pweil@redhat.com)
- Revert "Support deleting image stream status tags" (ccoleman@redhat.com)
- Remove "Pod" prefix from header on browse pod page (spadgett@redhat.com)
- Only try to update build if status message changed (rhcarvalho@gmail.com)
- Show status details for a DC in both the deployments table and DC pages
  (jforrest@redhat.com)
- Bug 1273787 - start deployment btn doesnt get enabled after dep finishes
  (jforrest@redhat.com)
- UPSTREAM: Proxy: do not send X-Forwarded-Host or X-Forwarded-Proto with an
  empty value (cewong@redhat.com)
- handle new non-resource urls (deads@redhat.com)
- UPSTREAM: 15958: add nonResourceURL detection (deads@redhat.com)
- Adjust line-height of route link to avoid clipping (spadgett@redhat.com)
- Support deleting image stream status tags (kargakis@tuta.io)
- tag: Support deleting a tag with -d (mkargaki@redhat.com)
- Bump K8s label selector to next version (sgoodwin@redhat.com)
- Add a container terminal to the pod details page (stefw@redhat.com)
- Remove old labels rendering from individual pages since its duplicate info
  (jforrest@redhat.com)
- Remove duplicate bootstrap.js from dependencies (spadgett@redhat.com)
- updated LDIF and tests (skuznets@redhat.com)
- Bug 1273350 - make click open the secondary nav instead of navigating
  (jforrest@redhat.com)
- Update label key/value pairs truncate at <769. Fixes
  https://github.com/openshift/origin/issues/5181 (sgoodwin@redhat.com)
- remove the deprecated build label on pods (bparees@redhat.com)
- UPSTREAM: 15621: Correctly handle empty source (ccoleman@redhat.com)
- UPSTREAM: 15953: Return unmodified error from negotiate (ccoleman@redhat.com)
- Fix exposing deployment configs (mkargaki@redhat.com)
- Remove code duplication (rhcarvalho@gmail.com)
- Fix patternfly CSS ordering (spadgett@redhat.com)
- expose: Set route port (mkargaki@redhat.com)
- Initial impl of viewing logs in web console (admin@benjaminapetersen.me)
- This commit implements birthcry for openshift proxy. This also addresses
  rhbz: https://bugzilla.redhat.com/show_bug.cgi?id=1270474
  (avagarwa@redhat.com)
- Bug 1271989 - error when navigating to resources in diff projects
  (jforrest@redhat.com)
- fix --config flag (deads@redhat.com)
- UPSTREAM: 15461: expose: Enable exposing multiport objects
  (mkargaki@redhat.com)
- client side changes for deployment logs (mkargaki@redhat.com)
- server side changes for deployment logs (mkargaki@redhat.com)
- api changes for deployment logs (mkargaki@redhat.com)
- Disable new upstream e2e tests (ccoleman@redhat.com)
- Remove authentication from import (ccoleman@redhat.com)
- Web console scaling (spadgett@redhat.com)
- Bug 1268891 - pods not always grouped when service selector should cover
  template of a dc/deployment (jforrest@redhat.com)
- ImageStream status.dockerImageRepository should always be local
  (ccoleman@redhat.com)
- remove kubectl apply from oc (deads@redhat.com)
- UPSTREAM: <drop>: disable kubectl apply until there's an impl
  (deads@redhat.com)
- Add ng-cloak to navbar to reduce flicker on load (spadgett@redhat.com)
- Disable v1beta3 in REST API (ironcladlou@gmail.com)
- help unit tests compile (maszulik@redhat.com)
- refactors (deads@redhat.com)
- UPSTREAM: openshift-sdn(TODO): update for iptables.New call
  (deads@redhat.com)
- UPSTREAM: openshift-sdn(TODO): handle boring upstream refactors
  (deads@redhat.com)
- UPSTREAM: 12221: Allow custom namespace creation in e2e framework
  (deads@redhat.com)
- UPSTREAM: 15807: Platform-specific setRLimit implementations
  (jliggitt@redhat.com)
- UPSTREAM: TODO: expose ResyncPeriod function (deads@redhat.com)
- UPSTREAM: 15451 <partial>: Add our types to kubectl get error
  (ccoleman@redhat.com)
- UPSTREAM: 14496: deep-copies: Structs cannot be nil (mkargaki@redhat.com)
- UPSTREAM: 11827: allow permissive SA secret ref limitting (deads@redhat.com)
- UPSTREAM: 12498: Re-add timeouts for kubelet which is not in the upstream PR.
  (deads@redhat.com)
- UPSTREAM: 15232: refactor logs to be composeable (deads@redhat.com)
- UPSTREAM: 8890: Allowing ActiveDeadlineSeconds to be updated for a pod
  (deads@redhat.com)
- UPSTREAM: <drop>: tweak generator to handle conversions in other packages
  (deads@redhat.com)
- UPSTREAM: <drop>: make test pass with old codec (deads@redhat.com)
- UPSTREAM: <drop>: add back flag types to reduce noise during this rebase
  (deads@redhat.com)
- UPSTREAM: <none>: Hack date-time format on *util.Time (ccoleman@redhat.com)
- UPSTREAM: <none>: Suppress aggressive output of warning (ccoleman@redhat.com)
- UPSTREAM: <carry>: v1beta3 (deads@redhat.com)
- UPSTREAM: <carry>: support pointing oc exec to old openshift server
  (deads@redhat.com)
- UPSTREAM: <carry>: Back n forth downward/metadata conversions
  (deads@redhat.com)
- UPSTREAM: <carry>: Disable --validate by default (mkargaki@redhat.com)
- UPSTREAM: <carry>: update describer for dockercfg secrets (deads@redhat.com)
- UPSTREAM: <carry>: reallow the ability to post across namespaces in api
  (pweil@redhat.com)
- UPSTREAM: <carry>: helper methods paralleling old latest fields
  (deads@redhat.com)
- UPSTREAM: <carry>: Add deprecated fields to migrate 1.0.0 k8s v1 data
  (jliggitt@redhat.com)
- UPSTREAM: <carry>: SCC (deads@redhat.com)
- UPSTREAM: <carry>: Allow pod start to be delayed in Kubelet
  (ccoleman@redhat.com)
- UPSTREAM: <carry>: Disable UIs for Kubernetes and etcd (deads@redhat.com)
- bump(k8s.io/kubernetes): 4c8e6f47ec23f390978e651232b375f5f9cde3c7
  (deads@redhat.com)
- bump(github.com/coreos/go-etcd): de3514f25635bbfb024fdaf2a8d5f67378492675
  (deads@redhat.com)
- bump(github.com/ghodss/yaml): 73d445a93680fa1a78ae23a5839bad48f32ba1ee
  (deads@redhat.com)
- bump(github.com/fsouza/go-dockerclient):
  1399676f53e6ccf46e0bf00751b21bed329bc60e (deads@redhat.com)
- bump(github.com/prometheus/client_golang):
  3b78d7a77f51ccbc364d4bc170920153022cfd08 (deads@redhat.com)
- Change api version in example apps (jhadvig@redhat.com)
- Bug 1270185 - service link on route details page missing project name
  (jforrest@redhat.com)
- make cherry-pick.sh easier to work with (deads@redhat.com)
- Minor deployment describer formatting fix (ironcladlou@gmail.com)
- Fix deployment config minor ui changes. (sgoodwin@redhat.com)
- Several fixes to the pods page (jforrest@redhat.com)
- test/cmd/export.sh shouldn't dump everything to STDOUT (ccoleman@redhat.com)
- Use the privileged SCC for all kube e2e tests (ccoleman@redhat.com)
- Preserve case of subresources when normalizing URLs (jliggitt@redhat.com)
- Output less info on hack/test-cmd.sh failures (ccoleman@redhat.com)
- Disable potentially insecure TLS cipher suites by default
  (ccoleman@redhat.com)
- Raw sed should not be used in hack/* scripts for Macs (ccoleman@redhat.com)
- Show container metrics in UI (spadgett@redhat.com)
- Fix provisions to be overrides (dmcphers@redhat.com)
- bump(github.com/openshift/openshift-sdn)
  62ec906f6563828364474ef117371ea2ad804dc8 (danw@redhat.com)
- Make image trigger test more reliable (ironcladlou@gmail.com)
- [RPMS] atomic-openshift services use openshift bin (sdodson@redhat.com)
- [RPMS] fix rpm build related to sdn restructure (sdodson@redhat.com)
- Fix fuzzing versions in serialization tests (pmorie@gmail.com)
- Show labels on all individual pages. Add label filtering to build config and
  deployment config pages. (jforrest@redhat.com)
- Provide initialized cloud provider in Kubelet config. (jsafrane@redhat.com)
- Fixes to the warning returned by the dc controller (mkargaki@redhat.com)
- Fix govet error (jliggitt@redhat.com)
- adding keystone IdP (sseago@redhat.com)
- Change to healthz as per @liggit comments. (smitram@gmail.com)
- Add a monitoring uri to the stats port. This allows us to not affect hosted
  backends but rather use the listener on the stats port to service health
  check requests. Of course the side effect here is that if you turn off stats,
  then the monitoring uri will not be available. (smitram@gmail.com)
- Bug 1259260 - when searching docker registry, should not exit in case of no
  matches (ffranz@redhat.com)
- Fix asset config warning (jliggitt@redhat.com)
- Configurable identity mapper strategies (jliggitt@redhat.com)
- Bump proxy resync from 30s to 10m (agoldste@redhat.com)
- Convert secondary nav to a hover menu (sgoodwin@redhat.com)
- remove useless ginkgo test for LDAP (skuznets@redhat.com)
- Sample app readme update (jhadvig@redhat.com)
- Fix s2i build with environment file extended test (mfojtik@redhat.com)
- Return error instead of generating arbitrary names (rhcarvalho@gmail.com)
- Replace local constant with constant from Kube (rhcarvalho@gmail.com)
- Godoc formatting (rhcarvalho@gmail.com)
- Print etcd version when calling openshift version (mfojtik@redhat.com)
- Use cmdutil.PrintSuccess() to display bulk output (ccoleman@redhat.com)
- Add SNI support (jliggitt@redhat.com)
- Build transport for etcd directly (jliggitt@redhat.com)
- Remove volume dir chcon from e2e-docker (agoldste@redhat.com)
- Always try to chcon the volume dir (agoldste@redhat.com)
- make ldap sync job accept group/foo whitelists (deads@redhat.com)
- Filter service endpoints when using multitenant plugin (danw@redhat.com)
- Update for osdn plugin argument changes (danw@redhat.com)
- Updated generated docs for openshift-sdn changes (danw@redhat.com)
- bump(github.com/openshift/openshift-sdn)
  5a41fee40db41b65578c07eff9fef35d183dce1c (danw@redhat.com)
- Generalize move-upstream.sh (ccoleman@redhat.com)
- move bash_completion.d/oc to clients package (tdawson@redhat.com)
- Add links to things from the overview and pod template (jforrest@redhat.com)
- deconflict swagger ports (deads@redhat.com)
- Scan for selinux write error in registry diagnostic. (dgoodwin@redhat.com)
- Add a cluster diagnostic to check if master is also running as a node.
  (dgoodwin@redhat.com)
- Report transient deployment trigger errors via API field
  (mkargaki@redhat.com)
- Add build timeout, by setting ActiveDeadlineSeconds on a build pod
  (maszulik@redhat.com)
- Update completions (ffranz@redhat.com)
- Append missing flags to cobra flags (jchaloup@redhat.com)
- added an LDAP host label (skuznets@redhat.com)
- add openshift group mapping for ldap sync (deads@redhat.com)
- Convert tables to 2 column layout at mobile res. And fix incorrect url to js
  files. (sgoodwin@redhat.com)
- add ldapsync blacklisting (deads@redhat.com)
- Move to openshift-jvm 1.0.29 (slewis@fusesource.com)
- bump(github.com/openshift/openshift-sdn)
  12f0efeb113058e04e9d333b92bbdddcfc34a9b4 (rpenta@redhat.com)
- Auto generated bash completion and examples doc for oadm pod-network
  (rpenta@redhat.com)
- Remove duplicated helper (rhcarvalho@gmail.com)
- union group name mapper (deads@redhat.com)
- UPSTREAM: 14871: Additional service ports config for master service.
  (abutcher@redhat.com)
- Update completions for kubernetes-service-node-port (abutcher@redhat.com)
- UPSTREAM: 13978 <drop>: NodePort option: Allowing for apiservers behind load-
  balanced endpoint. (abutcher@redhat.com)
- Update image stream page to use a table for the tags (jforrest@redhat.com)
- tighten ldap sync query types (deads@redhat.com)
- refactor building the syncer (deads@redhat.com)
- enhanced active directory ldap sync (deads@redhat.com)
- Use only official Dockerfile parser (rhcarvalho@gmail.com)
- Update the hacking guide (mkargaki@redhat.com)
- Support oadm pod-network cmd (rpenta@redhat.com)
- added extended tests for LDAP sync (skuznets@redhat.com)
- update ldif to work (deads@redhat.com)
- e2e util has unused import 'regexp' (ccoleman@redhat.com)
- add master API proxy client cert (jliggitt@redhat.com)
- Change CA lifetime defaults (jliggitt@redhat.com)
- UPSTREAM: 15224: Refactor SSH tunneling, fix proxy transport TLS/Dial
  extraction (jliggitt@redhat.com)
- UPSTREAM: 15224: Allow specifying scheme when proxying (jliggitt@redhat.com)
- UPSTREAM: 14889: Honor InsecureSkipVerify flag (jliggitt@redhat.com)
- UPSTREAM: 14967: Add util to set transport defaults (jliggitt@redhat.com)
- Fix for issue where pod template is clipped at mobile res.      - fix
  https://github.com/openshift/origin/issues/4489   - switch to pf-image icon
  - correct icon alignment in pod template        - align label and meta data
  on overview (sgoodwin@redhat.com)
- Fix issue where long text strings extend beyond pod template container at
  mobile res.  - remove flex and min/max width that are no longer needed
  (sgoodwin@redhat.com)
- OS support for host pid and ipc (pweil@redhat.com)
- UPSTREAM:<carry>:hostPid/hostIPC scc support (pweil@redhat.com)
- UPSTREAM:14279:IPC followup (pweil@redhat.com)
- UPSTREAM:<carry>:v1beta3 hostIPC (pweil@redhat.com)
- UPSTREAM:12470:Support containers with host ipc in a pod (pweil@redhat.com)
- UPSTREAM:<carry>:v1beta3 hostPID (pweil@redhat.com)
- UPSTREAM:13447:Allow sharing the host PID namespace (pweil@redhat.com)
- Specify scheme in the jolokia URL (slewis@fusesource.com)
- Fix tag and package name in new-build example (rhcarvalho@gmail.com)
- UPSTREAM: <drop>: disable oidc tests (jliggitt@redhat.com)
- Verify `oc get` returns OpenShift resources (ccoleman@redhat.com)
- UPSTREAM: 15451 <partial>: Add our types to kubectl get error
  (ccoleman@redhat.com)
- Add loading message to all individual pages (jforrest@redhat.com)
- Remove build history and deployment history from main tables
  (jforrest@redhat.com)
- add examples for rpm-based installs (jeder@redhat.com)
- status: Fix incorrect missing registry warning (mkargaki@redhat.com)
- Add configuration options for logging and metrics endpoints
  (spadgett@redhat.com)
- Fix masterCA conversion (jliggitt@redhat.com)
- Fix oc logs (jliggitt@redhat.com)
- Revert "Unique output image stream names in new-app" (ccoleman@redhat.com)
- Bug 1263562 - users without projects should get default ctx when logging in
  (ffranz@redhat.com)
- added LDAP entries for other schemas (skuznets@redhat.com)
- remove cruft from options (deads@redhat.com)
- provide feedback while the ldap group sync job is running (deads@redhat.com)
- Allow POST access to node stats for cluster-reader and system:node-reader
  (jliggitt@redhat.com)
- Update role bindings in compatibility test (jliggitt@redhat.com)
- Add cluster role bindings diagnostic (jliggitt@redhat.com)
- Fix template minification to keep line breaks, remove html files from bindata
  (jforrest@redhat.com)
- Post 4902 fixes (maszulik@redhat.com)
- Add oc rsync command (cewong@redhat.com)
- bump(github.com/openshift/source-to-image)
  1fd4429c584d688d83c1247c03fa2eeb0b083ccb (cewong@redhat.com)
- Fixing typos (dmcphers@redhat.com)
- allocate supplemental groups to namespace (pweil@redhat.com)
- Remove forgotten code no longer used (nagy.martin@gmail.com)
- assets: Fix null dereference in updateTopology() (stefw@redhat.com)
- make oc logs support builds and buildconfigs (deads@redhat.com)
- Wait until the slave pod is gone (nagy.martin@gmail.com)
- UPSTREAM: 14616: Controller framework test flake fix (mfojtik@redhat.com)
- Disable verbose extended run (mfojtik@redhat.com)
- Unique output image stream names in new-app (rhcarvalho@gmail.com)
- Fix start build extended test (mfojtik@redhat.com)
- Make cleanup less noisy (mfojtik@redhat.com)
- Replace default reporter in Ginkgo with SimpleReporter (mfojtik@redhat.com)
- Atomic feature flags followup (miminar@redhat.com)
- examples: Move hello-openshift example to API v1 (stefw@redhat.com)
- Fix Vagrant provisioning after move to contrib/vagrant (dcbw@redhat.com)
- Always bring up openshift's desired network configuration on Vagrant
  provision (dcbw@redhat.com)
- Add annotations to the individual pages (jforrest@redhat.com)
- OS swagger and descriptions (pweil@redhat.com)
- UPSTREAM:<carry>:introduce scc types for fsgroup and supplemental groups
  (pweil@redhat.com)
- ldap sync active directory (deads@redhat.com)
- Change connection-based kubelet auth to application-level authn/authz
  interfaces (jliggitt@redhat.com)
- UPSTREAM: 15232`: refactor logs to be composeable (deads@redhat.com)
- bump(github.com/hashicorp/golang-lru):
  7f9ef20a0256f494e24126014135cf893ab71e9e (jliggitt@redhat.com)
- UPSTREAM: 14700: Add authentication/authorization interfaces to kubelet,
  always include /metrics with /stats (jliggitt@redhat.com)
- UPSTREAM: 14134: sets.String#Intersection (jliggitt@redhat.com)
- UPSTREAM: 15101: Add bearer token support for kubelet client config
  (jliggitt@redhat.com)
- UPSTREAM: 14710: Add verb to authorizer attributes (jliggitt@redhat.com)
- UPSTREAM: 13885: Cherry pick base64 and websocket patches
  (ccoleman@redhat.com)
- Delete --all option for oc export in cli doc (nakayamakenjiro@gmail.com)
- Fix cadvisor in integration test (jliggitt@redhat.com)
- Disable --allow-missing-image test (cewong@redhat.com)
- Make kube-proxy iptables sync period configurable (mkargaki@redhat.com)
- Update to latest version of PatternFly 2.2.0 and Bootstrap  3.3.5
  (sgoodwin@redhat.com)
- PHP hot deploy extended test (jhadvig@redhat.com)
- Ruby hot deploy extended test (jhadvig@redhat.com)
- change show-all default to true (deads@redhat.com)
- Update post-creation messages for builds in CLI (rhcarvalho@gmail.com)
- [Bug 4959] sample-app/cleanup.sh: fix usage of not-installed killall command.
  (vsemushi@redhat.com)
- fix bad oadm line (max.andersen@gmail.com)
- Refactored Openshift Origin builder, decoupled from S2I builder, added mocks
  and testing (kirill.frolov@servian.com)
- Use correct master url for internal token request, set master CA correctly
  (jliggitt@redhat.com)
- fix non-default all-in-one ports for testing (deads@redhat.com)
- Add extended test for git authentication (cewong@redhat.com)
- reconcile-cluster-role-bindings command (jliggitt@redhat.com)
- Change validation timing on create from image page (spadgett@redhat.com)
- Issue 2378 - Show TLS information for routes, create routes and
  routes/routename pages (jforrest@redhat.com)
- Lowercase resource names (rhcarvalho@gmail.com)
- create local images as docker refs (bparees@redhat.com)
- Preserve deployment status sequence (mkargaki@redhat.com)
- Add tests for S2I Perl and Python images with Hot Deploy
  (nagy.martin@gmail.com)
- Test asset config (jliggitt@redhat.com)
- UPSTREAM: 14967: Add util to set transport defaults (jliggitt@redhat.com)
- UPSTREAM: 14246: Fix race in lifecycle admission test (mfojtik@redhat.com)
- Fix send to closed channel in waitForBuild (mfojtik@redhat.com)
- UPSTREAM: 13885: Update error message in wsstream for go 1.5
  (mfojtik@redhat.com)
- Fix go vet (jliggitt@redhat.com)
- Change to use a 503 error page to fully address #4215 This allows custom
  error pages to be layered on in custom haproxy images. (smitram@gmail.com)
- Reduce number of test cases and add cleanup - travis seems to be hitting
  memory errors with starting multiple haproxy routers. (smitram@gmail.com)
- Fixes as per @Miciah review comments. (smitram@gmail.com)
- Update generated completions. (smitram@gmail.com)
- Add/update f5 tests for partition path. (smitram@gmail.com)
- Add partition path support to the f5 router - this will also allows us to
  support sharded routers with f5 using different f5 partitions.
  (smitram@gmail.com)
- Fixes as per @smarterclayton & @pweil- review comments and add generated docs
  and bash completions. (smitram@gmail.com)
- Turn on haproxy statistics by default since its now on a protected page.
  (smitram@gmail.com)
- Bind to router stats options (fixes issue #4884) and add help text
  clarifications. (smitram@gmail.com)
- Add tabs to pod details page (spadgett@redhat.com)
- Bug 1268484 - Use build.metadata.uid to track dismissed builds in UI
  (spadgett@redhat.com)
- cleanup ldap sync validation (deads@redhat.com)
- update auth test to share long running setup (deads@redhat.com)
- make ldap sync-group work (deads@redhat.com)
- fix ldap sync types to be more understandable (deads@redhat.com)
- remove unused mapper (pweil@redhat.com)
- change from kind to resource (pweil@redhat.com)
- fix decoding to handle yaml (deads@redhat.com)
- UPSTREAM: go-ldap: add String for debugging (deads@redhat.com)
- UPSTREAM: 14451: Fix a race in pod backoff. (mfojtik@redhat.com)
- Fix unbound variable in hack/cherry-pick.sh (mfojtik@redhat.com)
- Cleanup godocs of build types (rhcarvalho@gmail.com)
- Update travis to go 1.5.1 (mfojtik@redhat.com)
- Enable Go 1.5 (ccoleman@redhat.com)
- UPSTREAM: Fix typo in e2e pods test (nagy.martin@gmail.com)
- rename allow-missing to allow-missing-images (bparees@redhat.com)
- prune images: Conform to the hacking guide (mkargaki@redhat.com)
- Drop imageStream.spec.dockerImageRepository tags/IDs during conversion
  (ccoleman@redhat.com)
- Add validation to prevent IS.spec.dockerImageRepository from having tags
  (ccoleman@redhat.com)
- Add a helper to move things upstream (ccoleman@redhat.com)
- Cherry-pick helper (ccoleman@redhat.com)
- Clean up root folder (ccoleman@redhat.com)
- UPSTREAM: 13885: Support websockets on exec and pod logs
  (ccoleman@redhat.com)
- add test for patching anonymous fields in structs (deads@redhat.com)
- UPSTREAM: 14985: fix patch for anonymous struct fields (deads@redhat.com)
- fix exec admission controller flake (deads@redhat.com)
- updated template use (skuznets@redhat.com)
- fixed go vet invocation and errors (skuznets@redhat.com)
- Add ethtool to base/Dockerfile.rhel7 too (sdodson@redhat.com)
- UPSTREAM: 14831: allow yaml as argument to patch (deads@redhat.com)
- Wait for service account to be accessible (mfojtik@redhat.com)
- Wait for builder account (mfojtik@redhat.com)
- Pull RHEL7 images from internal CI registry (mfojtik@redhat.com)
- Initial addition of S2I SCL enablement extended tests (mfojtik@redhat.com)
- tolerate missing docker images (bparees@redhat.com)
- bump(github.com/spf13/cobra): d732ab3a34e6e9e6b5bdac80707c2b6bad852936
  (ffranz@redhat.com)
- allow SAR requests in lifecycle admission (pweil@redhat.com)
- Issue 4001 - add requests and limits to resource limits on settings page
  (jforrest@redhat.com)
- prevent force pull set up from running in other focuses; add some debug clues
  in hack/util.sh; comments from Cesar, Ben; create new builder images so we
  run concurrent;  MIchal's comments; move to just one builder
  (gmontero@redhat.com)
- fix govet example error (skuznets@redhat.com)
- Add Restart=always to master service (sdodson@redhat.com)
- Issue 4867 - route links should open in a new window (jforrest@redhat.com)
- Fix output of git basic credentials in builder (cewong@redhat.com)
- Add fibre channel guide (hchen@redhat.com)
- Add Cinder Persistent Volume guide (jsafrane@redhat.com)
- Move NFS documentation to a subchapter. (jsafrane@redhat.com)
- Set build status message in case of error (rhcarvalho@gmail.com)
- Fix the reference of openshift command in Makefile (akira@tagoh.org)
- Issue 4632 - remove 'Project' from the project overview header
  (jforrest@redhat.com)
- Issue 4860 - missing no deployments msg when only have RCs
  (jforrest@redhat.com)
- Support deployment hook volume inheritance (ironcladlou@gmail.com)
- fix RAR test flake (deads@redhat.com)
- UPSTREAM: 14688: Deflake max in flight (deads@redhat.com)
- Fix vagrant provisioning (danw@redhat.com)
- setup makefile to be parallelizeable (deads@redhat.com)
- api group support for authorizer (deads@redhat.com)
- Apply OOMScoreAdjust and Restart policy to openshift node (decarr@redhat.com)
- Fix nit (dmcphers@redhat.com)
- Add ethtool to our deps (mkargaki@redhat.com)
- Issue 4855 - warning flickers about build config and deployment config not
  existing (jforrest@redhat.com)
- Add MySQL extended replication tests (nagy.martin@gmail.com)
- extended: Disable Daemon tests (mkargaki@redhat.com)
- Add environment values to oc new-app help for mysql
  (nakayamakenjiro@gmail.com)
- Update oadm router and registry help message (nakayamakenjiro@gmail.com)
- Adds explicit suggestions for some cli commands (ffranz@redhat.com)
- bump(github.com/spf13/pflag): b084184666e02084b8ccb9b704bf0d79c466eb1d
  (ffranz@redhat.com)
- bump(github.com/cpf13/cobra): 046a67325286b5e4d7c95b1d501ea1cd5ba43600
  (ffranz@redhat.com)
- Don't show errors in name field until blurred (spadgett@redhat.com)
- Allow whitespace-only values in UI for required parameters
  (spadgett@redhat.com)
- make RAR allow evaluation errors (deads@redhat.com)
- Watch routes on individual service page (spadgett@redhat.com)
- bump(github.com/vjeantet/ldapserver) 19fbc46ed12348d5122812c8303fb82e49b6c25d
  (mkargaki@redhat.com)
- Do not treat directories named Dockerfile as file (rhcarvalho@gmail.com)
- Bug 1266859: UPSTREAM: <drop>: expose: Truncate service names
  (mkargaki@redhat.com)
- Enable cpu cfs quota by default (decarr@redhat.com)
- Disable the pods per node test - it requires the kubelet stats
  (ccoleman@redhat.com)
- Update docs regarding the rebase (mkargaki@redhat.com)
- Set Build.Status.Pushspec to resolved pushspec (rhcarvalho@gmail.com)
- Bug: 1266442 1266447 (jhadvig@redhat.com)
- new-app: Better output in case of invalid Dockerfile (mkargaki@redhat.com)
- Compatibility test for Volume Source (mkargaki@redhat.com)
- Update UPGRADE.md about Metadata/Downward (mkargaki@redhat.com)
- get local IP like the server would and add retries to build test watch
  (pweil@redhat.com)
- Interesting refactoring (mkargaki@redhat.com)
- Fix verify-open-ports.sh to not fail on success (mkargaki@redhat.com)
- Boring refactoring; code generations (mkargaki@redhat.com)
- UPSTREAM: openshift-sdn: 167: plugins: Update Kube client imports
  (mkargaki@redhat.com)
- UPSTREAM: <carry>: Move to test pkg to avoid linking test flags in binaries
  (pweil@redhat.com)
- UPSTREAM: <carry>: Add etcd prefix (mkargaki@redhat.com)
- UPSTREAM: 14664: fix testclient prepend (deads@redhat.com)
- UPSTREAM: 14502: don't fatal on missing sorting flag (deads@redhat.com)
- UPSTREAM: <drop>: hack experimental versions and client creation
  (deads@redhat.com)
- UPSTREAM: 14496: deep-copies: Structs cannot be nil (mkargaki@redhat.com)
- UPSTREAM: <carry>: Back n forth downward/metadata conversions
  (mkargaki@redhat.com)
- UPSTREAM: 13728: Allow to replace os.Exit() with panic when CLI command fatal
  (mfojtik@redhat.com)
- UPSTREAM: 14291: add patch verb to APIRequestInfo (deads@redhat.com)
- UPSTREAM: 13910: Fix resourcVersion = 0 in cacher (mkargaki@redhat.com)
- UPSTREAM: 13864: Fix kubelet logs --follow bug (mkargaki@redhat.com)
- UPSTREAM: 14063: enable system CAs (mkargaki@redhat.com)
- UPSTREAM: 13756: expose: Avoid selector resolution if a selector is not
  needed (mkargaki@redhat.com)
- UPSTREAM: 13746: Fix field=metadata.name (ccoleman@redhat.com)
- UPSTREAM: 9870: Allow Volume Plugins to be configurable (deads@redhat.com)
- UPSTREAM: 11827: allow permissive SA secret ref limitting (deads@redhat.com)
- UPSTREAM: 12221: Allow custom namespace creation in e2e framework
  (mfojtik@redhat.com)
- UPSTREAM: 12498: Re-add timeouts for kubelet which is not in the upstream PR.
  (deads@redhat.com)
- UPSTREAM: 9009: Retry service account update when adding token reference
  (deads@redhat.com)
- UPSTREAM: 9844: EmptyDir volume SELinux support (deads@redhat.com)
- UPSTREAM: 7893: scc allocation interface methods (deads@redhat.com)
- UPSTREAM: 7893: scc (pweil@redhat.com)
- UPSTREAM: 8890: Allowing ActiveDeadlineSeconds to be updated for a pod
  (deads@redhat.com)
- UPSTREAM: <drop>: add back flag types to reduce noise during this rebase
  (deads@redhat.com)
- UPSTREAM: <none>: Hack date-time format on *util.Time (ccoleman@redhat.com)
- UPSTREAM: <none>: Suppress aggressive output of warning (ccoleman@redhat.com)
- UPSTREAM: <carry>: Disable --validate by default (mkargaki@redhat.com)
- UPSTREAM: <carry>: update describer for dockercfg secrets (deads@redhat.com)
- UPSTREAM: <carry>: reallow the ability to post across namespaces in api
  (pweil@redhat.com)
- UPSTREAM: <carry>: support pointing oc exec to old openshift server
  (deads@redhat.com)
- UPSTREAM: <carry>: Add deprecated fields to migrate 1.0.0 k8s v1 data
  (jliggitt@redhat.com)
- UPSTREAM: <carry>: Allow pod start to be delayed in Kubelet
  (ccoleman@redhat.com)
- UPSTREAM: <carry>: Disable UIs for Kubernetes and etcd (deads@redhat.com)
- UPSTREAM: <carry>: v1beta3 (deads@redhat.com)
- bump(github.com/emicklei/go-restful) 1f9a0ee00ff93717a275e15b30cf7df356255877
  (mkargaki@redhat.com)
- bump(k8s.io/kubernetes) 86b4e777e1947c1bc00e422306a3ca74cbd54dbe
  (mkargaki@redhat.com)
- Update java console (slewis@fusesource.com)
- fix QueryForEntries API (deads@redhat.com)
- added sync-groups command basics (skuznets@redhat.com)
- add ldap groups sync (skuznets@redhat.com)
- Remove templates.js from bindata and fix HTML minification
  (spadgett@redhat.com)
- fedora 21 Vagrant provisioning fixes (dcbw@redhat.com)
- add timing statements (deads@redhat.com)
- Issue 4795 - include ref and contextdir in github links (jforrest@redhat.com)
- new-app: Actually use the Docker parser (mkargaki@redhat.com)
- Update old references to _output/local/go/bin (rhcarvalho@gmail.com)
- improved robustness of recycler script (mturansk@redhat.com)
- Do not export test utility (rhcarvalho@gmail.com)
- Routes should be able to specify which port they desire (ccoleman@redhat.com)
- Change build-go to generate binaries to _output/local/bin/${platform}
  (ccoleman@redhat.com)
- Make deployment trigger logging quieter (ironcladlou@gmail.com)
- bump(github.com/openshift/openshift-sdn)
  669deb4de23ab7f79341a132786b198c7f272082 (rpenta@redhat.com)
- Fix openshift-sdn imports in origin (rpenta@redhat.com)
- Move plugins/osdn to Godeps/workspace/src/github.com/openshift/openshift-
  sdn/plugins/osdn (rpenta@redhat.com)
- Move sdn ovssubnet to pkg/ovssubnet dir (rpenta@redhat.com)
- Source info should only be loaded when Git is used for builds
  (ccoleman@redhat.com)
- Reorganize web console create flow (spadgett@redhat.com)
- Fix handle on watchObject. Set deletionTimestamp instead of deleted.
  (jforrest@redhat.com)
- Use direct CLI invocations rather than embedding CLI (ccoleman@redhat.com)
- Next steps page (after creating stuff in console) (ffranz@redhat.com)
- Disable parallelism for now (ccoleman@redhat.com)
- Do not require the master components from test/util (ccoleman@redhat.com)
- [userinterface_public_538] Create individual pages for all resources With
  some changes from @sg00dwin and @spadgett (jforrest@redhat.com)
- Fix some of the govet issues (mfojtik@redhat.com)
- annotate builds on clone (bparees@redhat.com)
- Make network fixup during provision conditional (marun@redhat.com)
- Update roadmap url (dmcphers@redhat.com)
- better error message for immutable edits to builds (bparees@redhat.com)
- Default NetworkConfig.ServiceNetworkCIDR to
  KubernetesMasterConfig.ServicesSubnet (jliggitt@redhat.com)
- create SCCExecRestriction admission plugin (deads@redhat.com)
- added oadm commands to validate node and master config (skuznets@redhat.com)
- Add an e2e test for Dockerfile and review comments (ccoleman@redhat.com)
- Add extended tests for start-build (mfojtik@redhat.com)
- allow local access reviews while namespace is terminating (deads@redhat.com)
- build oc, move to clients, move alt clients to redistributable
  (tdawson@redhat.com)
- Add --kubeconfig support for compat with kubectl (ccoleman@redhat.com)
- assets: Filter topology correctly and refactor relations (stefw@redhat.com)
- allow self SARs using old policy: (deads@redhat.com)
- Capture panic in extended CLI and return them as Go errors
  (mfojtik@redhat.com)
- UPSTREAM: 13728: Allow to replace os.Exit() with panic when CLI command fatal
  (mfojtik@redhat.com)
- Expose version as prometheus metric (jimmidyson@gmail.com)
- Take stdin on OpenShift CLI (ccoleman@redhat.com)
- add extended tests for example repos (bparees@redhat.com)
- added syntax highlighting to readme (skuznets@redhat.com)
- Retry finalizer on conflict error (decarr@redhat.com)
- Build from a Dockerfile directly (ccoleman@redhat.com)
- fix backwards poll args (bparees@redhat.com)
- Add missing rolling hook conversions (ironcladlou@gmail.com)
- Make "default" an admin namespace in multitenant (danw@redhat.com)
- add patch to default roles (deads@redhat.com)
- Exclude a few more tests (ccoleman@redhat.com)
- Refactor setting and resetting HTTP proxies (rhcarvalho@gmail.com)
- UPSTREAM: 14291: add patch verb to APIRequestInfo (deads@redhat.com)
- Add --portal-net back to all-in-one args (danw@redhat.com)
- Bump kubernetes-ui-label-selector to v0.0.10 - fixes js error
  (jforrest@redhat.com)
- Fix broken link in readme (mtayer@redhat.com)
- add SA role bindings to auto-provisioned namespaces (deads@redhat.com)
- diagnostics: fail gracefully on broken kubeconfig (lmeyer@redhat.com)
- Improve systemd detection for diagnostics. (dgoodwin@redhat.com)
- Refactor pkg/build/builder (rhcarvalho@gmail.com)
- Set kubeconfig in extended tests (ccoleman@redhat.com)
- Extended failure (ccoleman@redhat.com)
- Only run k8s upstream tests that are passing (ccoleman@redhat.com)
- Add example env vars (rhcarvalho@gmail.com)
- Pass env vars defined in Docker build strategy (rhcarvalho@gmail.com)
- [RPMs] Ease the upgrade to v1.0.6 (sdodson@redhat.com)
- BZ1221441 - new filter that shows unique project name (rafabene@gmail.com)
- Push F5 image (ccoleman@redhat.com)
- Making the regex in ./test/cmd/admin.sh a little more flexible for downstream
  (bleanhar@redhat.com)
- Add generated-by annotation to CLI new-app and web console
  (mfojtik@redhat.com)
- more comments (pweil@redhat.com)
- Gluster Docs (screeley@redhat.com)
- add cluster roles to diagnostics (deads@redhat.com)
- UPSTREAM: 14063: enable system CAs (deads@redhat.com)
- Linux 386 cross compile (ccoleman@redhat.com)
- Add X-Forwarded-* headers and the new Forwarded header for rfc7239 so that
  the backend has info about the proxied request (and requestor).
  (smitram@gmail.com)
- switch to https for sample repo url (bparees@redhat.com)
- Add SA secret checking to SA readiness test in integration tests
  (cewong@redhat.com)
- Adding source secret (jhadvig@redhat.com)
- disable go vet in make check-test (skuznets@redhat.com)
- Update bash-completion (nakayamakenjiro@gmail.com)
- Allow metadata on images to be edited after creation (ccoleman@redhat.com)
- Enable linux-386 (ccoleman@redhat.com)
- .commit is a file, not a directory (ccoleman@redhat.com)
- Retry deployment resource updates (ironcladlou@gmail.com)
- Improve latest deployment output (ironcladlou@gmail.com)
- Make release extraction a separate step for builds (ccoleman@redhat.com)
- bump(github.com/openshift/openshift-sdn)
  0f9e6558e8dceb8c8317e3587d9c9c94ae07ecb8 (rpenta@redhat.com)
- Fix potential race conditions during SDN setup (rpenta@redhat.com)
- Fix casing of output (ironcladlou@gmail.com)
- Adjust help templates to latest version of Cobra (ffranz@redhat.com)
- Update generated completions (ffranz@redhat.com)
- bump(github.com/spf13/cobra): 6d7031177028ad8c5b4b428ac9a2288fbc1c0649
  (ffranz@redhat.com)
- bump(github.com/spf13/pflag): 8e7dc108ab3a1ab6ce6d922bbaff5657b88e8e49
  (ffranz@redhat.com)
- Update to version 0.0.9 for kubernetes-label-selector. Fixes issue
  https://github.com/openshift/origin/issues/3180 (sgoodwin@redhat.com)
- UPSTREAM: 211: Allow listen only ipv4 (ccoleman@redhat.com)
- UPSTREAM: Disable systemd activation for DNS (ccoleman@redhat.com)
- bump(github.com/skynetservices/skydns):bb2ebadc9746f23e4a296e3cbdb8c01e956bae
  e1 (jimmidyson@gmail.com)
- Fixes #4494: Don't register skydns metrics on nodes (jimmidyson@gmail.com)
- Move positional parameters before package lists (nagy.martin@gmail.com)
- Simplify the readme to point to docs (ccoleman@redhat.com)
- Normalize extended tests into test/extended/*.sh (ccoleman@redhat.com)
- Improve deploy --cancel output (ironcladlou@gmail.com)
- Bump min Docker version in docs (agoldste@redhat.com)
- Normalize extended tests into test/extended/*.sh (ccoleman@redhat.com)
- Return empty Config field in FromName to avoid nil pointer error
  (nakayamakenjiro@gmail.com)
- docs: Fixed broken links in openshift_model.md. (stevem@gnulinux.net)
- Show corrent error message if passed json template is invalid
  (prukner.jan@seznam.cz)
- Clean up test directories (ccoleman@redhat.com)
- hack/build-images.sh fails on vboxfs due to hardlink (ccoleman@redhat.com)
- Fail with stack trace in test bash (ccoleman@redhat.com)
- Make oc rsh behave more like ssh (ccoleman@redhat.com)
- better error messages for parameter errors (bparees@redhat.com)
- Simplify the release output, create a zip (ccoleman@redhat.com)
- Include zip in the origin/release image (ccoleman@redhat.com)
- Update bindata (slewis@fusesource.com)
- Drop BuildConfig triggers of unknown type (cewong@redhat.com)
- escape quotes in docker labels (bparees@redhat.com)
- Cleaning useless colon (remy.binsztock@tech-angels.com)
- Fix oadm router F5 flags (miciah.masters@gmail.com)
- Compatibility: Handle invalid build ConfigChange trigger. (cewong@redhat.com)
- app: Implement initial topology-graph based view (stefw@redhat.com)
- app: Normalize kind property on retrieved items (stefw@redhat.com)
- app: Toggle overview modes between tiles and topology (stefw@redhat.com)
- Update bindata (slewis@fusesource.com)
- Removed debug logging (slewis@fusesource.com)
- Update openshift-jvm (slewis@fusesource.com)
- Make logo selector #header-logo and reduce specificity (sgoodwin@redhat.com)
- fix examples (pweil@redhat.com)
- Only show java console link if the pod is running, for #4612
  (slewis@fusesource.com)
- Bug 1256303: prune images: Tolerate missing bc/build errors for AEP
  (mkargaki@redhat.com)
- bump(github.com/openshift/source-to-image)
  847bf029b540c689f1644419efd2e70b64b90547 (mfojtik@redhat.com)
- scale: Doc scaling a config with no deployments (mkargaki@redhat.com)
- Rename gitconfig secret key to .gitconfig (cewong@redhat.com)
- UPSTREAM: google/cadvisor: 844: Fix cadvisor bug with advancing clocks
  (jliggitt@redhat.com)
- Update to openshift-jvm 1.0.22 (slewis@fusesource.com)
- add sample repo annotation to imagestreams (bparees@redhat.com)
- Update ClusterNetwork record when upgrading from 3.0.0 (danw@redhat.com)
- Add extended network tests (marun@redhat.com)
- Enable connectivity between dind master and pods (marun@redhat.com)
- Allow cluster instance prefix to be overriden (marun@redhat.com)
- Clean up pushd/popd stdout noise in cluster create (marun@redhat.com)
- Isolate dind cluster config (marun@redhat.com)
- Fix extended test infrastructure (marun@redhat.com)
- Test for exposing external services (mkargaki@redhat.com)
- Revert LDAP OAuth field rename (jliggitt@redhat.com)
- UPSTREAM: 13756: expose: Avoid selector resolution if a selector is not
  needed (mkargaki@redhat.com)
- Make oc edit cmd follow the hacking guide (bbartl.roman@gmail.com)
- added openldap fixtures and test (skuznets@redhat.com)
- Update to k8s-label-selector 0.0.8 (spadgett@redhat.com)
- bump(github.com/openshift/openshift-sdn)
  e6604ec1114b1141c735114c08dc717a9a717929 (rpenta@redhat.com)
- make end-to-end-docker a full test (deads@redhat.com)
- Populated kubernetes pod network status for SDN multitenant plugin
  (rpenta@redhat.com)
- Port upstream rolling updater enhancements (ironcladlou@gmail.com)
- Allow field labels to work for routes (ccoleman@redhat.com)
- UPSTREAM: 13746: Fix field=metadata.name (ccoleman@redhat.com)
- Ignore 404 on list of resources during delete (decarr@redhat.com)
- Fixes JS error in deployments page (ffranz@redhat.com)
- update repo address (pweil@redhat.com)
- Clean up edge cases on overview to match new simplified look
  (jforrest@redhat.com)
- Remove index.html from Java console URL (spadgett@redhat.com)
- UPSTREAM: 11942: Rolling updater availability enhancements
  (ironcladlou@gmail.com)
- Fix inconsistancy in secrets pkg (jhadvig@redhat.com)
- Remove os.Exit(1) from start-build --wait (mfojtik@redhat.com)
- Add --wait option to start-build (mfojtik@redhat.com)
- UPSTREAM: 13705: Add pods/attach to long running requests, protect in
  admission for privileged pods (jliggitt@redhat.com)
- Add pods/attach to admin/edit roles (jliggitt@redhat.com)
- Add Cancel button to UI for running builds (spadgett@redhat.com)
- Disable deployment retry on web console until we have an api
  (contact@fabianofranz.com)
- Deploy, rollback, retry and cancel deployments from the web console
  (ffranz@redhat.com)
- Issue 4365 - example github url as a link is really confusing
  (jforrest@redhat.com)
- diagnostics: print stack trace on panic (lmeyer@redhat.com)
- limit test-cmd.sh to the master on non-default ports (deads@redhat.com)
- Move unique host functionality out of router plugin (ccoleman@redhat.com)
- Use route.Spec internally (ccoleman@redhat.com)
- Prevent aggressive wrapping of long project names before they have to. Fixes
  https://github.com/openshift/origin/issues/4541 (sgoodwin@redhat.com)
- Reduce whitespace on overview and collapse pods by their status Added popup
  with warning details Fix firefox 40 double underline on abbr tags ( bug
  1260349 ) (jforrest@redhat.com)
- Put resource names in generated config, select endpoint using apiVersion
  (jliggitt@redhat.com)
- Rename type to resource (jliggitt@redhat.com)
- UPSTREAM: 12845: Export KindToResource (jliggitt@redhat.com)
- Validate ICTs of DockerStrategy BuildConfigs (rhcarvalho@gmail.com)
- Fix missing port error when validating source url (mfojtik@redhat.com)
- Add --commit option to start-build (mfojtik@redhat.com)
- Add "View all projects" link to projects dropdown (spadgett@redhat.com)
- Removing whitespaces in project describe (jhadvig@redhat.com)
- Bug 1250652: Scale dc template in case of no deployment (mkargaki@redhat.com)
- Make unknown trigger types to be warning not error (rhcarvalho@gmail.com)
- Add volume size option (dmcphers@redhat.com)
- don't test the git connection when a proxy is set (bparees@redhat.com)
- Use <name>-<namespace> instead of <name>.<namespace> in routes
  (ccoleman@redhat.com)
- split extended tests into functional areas (deads@redhat.com)
- Filter routes by namespace or project labels (ccoleman@redhat.com)
- Surface ConfigChange trigger in new app, render in build page
  (jliggitt@redhat.com)
- Tests for adding envVars to buildConfig via new-build (jhadvig@redhat.com)
- Add --env flag to the new-build (jhadvig@redhat.com)
- Fix broken SDN on multinode vagrant environment (rpenta@redhat.com)
- Bug 1250291 - labels must be applied to templates in deploymentconfigs
  (ffranz@redhat.com)
- Issue 3114 - watch should return cached data immediately
  (jforrest@redhat.com)
- Add helper script to run kube e2e tests (marun@redhat.com)
- Fix docs of oc (prukner.jan@seznam.cz)
- Handle multiple paths together (ccoleman@redhat.com)
- Add AuthService.withUser() call to CreateProjectController
  (spadgett@redhat.com)
- fix process kill in old e2e.sh (deads@redhat.com)
- UPSTREAM: 13322: Various exec fixes (jliggitt@redhat.com)
- bump(github.com/fsouza/go-dockerclient):
  76fd6c68cf24c48ee6a2b25def997182a29f940e (jliggitt@redhat.com)
- make impersonateSAR with empty token illegal (deads@redhat.com)
- improve nodeconfig validation (deads@redhat.com)
- Check pointer before using it (rhcarvalho@gmail.com)
- get: Fix imageStream tag clutter (mkargaki@redhat.com)
- Issue 2683 - deprecation warning from moment.js (jforrest@redhat.com)
- Fix manual deployment (ironcladlou@gmail.com)
- Fix copy-paste in test (rhcarvalho@gmail.com)
- UPSTREAM(docker/distribution): manifest deletions (agoldste@redhat.com)
- UPSTREAM(docker/distribution): custom routes/auth (agoldste@redhat.com)
- UPSTREAM(docker/distribution): add BlobService (agoldste@redhat.com)
- UPSTREAM(docker/distribution): add layer unlinking (agoldste@redhat.com)
- UPSTREAM: add context to ManifestService methods (rpenta@redhat.com)
- bump(github.com/AdRoll/goamz/{aws,s3}):cc210f45dcb9889c2769a274522be2bf70edfb
  99 (mkargaki@redhat.com)
- switch integration tests to non-default ports (deads@redhat.com)
- new-app: Fix oc expose recommendation (mkargaki@redhat.com)
- Allow customization of login page (spadgett@redhat.com)
- [RPMs] Fix requirements between node and tuned profiles (sdodson@redhat.com)
- Fix token display page (jliggitt@redhat.com)
- integration/diag_nodes_test.go: fix test flake issue 4499 (lmeyer@redhat.com)
- Remove background-size and include no-repeat (sgoodwin@redhat.com)
- enable docker registry wait in forcepull bucket (skuznets@redhat.com)
- bump(github.com/docker/distribution):1341222284b3a6b4e77fb64571ad423ed58b0d34
  (mkargaki@redhat.com)
- Secret help - creating .dockercfg from file should be done via 'oc secrets
  new' (jhadvig@redhat.com)
- Add bcrypt to htpasswd auth (jimmidyson@gmail.com)
- Renaming osc to oc in cmd code (jhadvig@redhat.com)
- Prevent duplicate routes from being exposed (ccoleman@redhat.com)
- use buildlog_level field for docker build log level (bparees@redhat.com)
- Fix for nav bar issues on resize.
  https://github.com/openshift/origin/issues/4404 - Styling details of filter,
  add to project, and toggle menu - Use of flex for positioning
  (sgoodwin@redhat.com)
- Router can filter on namespace, label, field (ccoleman@redhat.com)
- Added --generator to expose command as receive error message. Added used of
  v2 tagged image and different color to further emphasize the difference.
  (sspeiche@redhat.com)
- UPSTREAM: 9870: PV Recycler config (mturansk@redhat.com)
- UPSTREAM: 12603: Expanded volume.Spec (mturansk@redhat.com)
- UPSTREAM: 13310: Added VolumeConfig to Volumes (mturansk@redhat.com)
- UPSTREAM: revert 9c1056e: 12603: Expanded volume.Spec to full Volume and PV
  (mturansk@redhat.com)
- UPSTREAM: revert 3b01c2c: 9870: configurable pv recyclers
  (mturansk@redhat.com)
- implementation of deleting from settings using modal
  (gabriel_ruiz@symantec.com)
- better build-logs error messages (bparees@redhat.com)
- Support additional source secret files in builds (cewong@redhat.com)
- expose project creation failures (deads@redhat.com)
- diagnostics: fix, make tests happy (lmeyer@redhat.com)
- diagnostics: remove log message format helpers (lmeyer@redhat.com)
- diagnostics: remove machine-readable output formats (lmeyer@redhat.com)
- diagnostics: revise per code reviews (lmeyer@redhat.com)
- diagnostics: k8s repackaged (lmeyer@redhat.com)
- diagnostics: add registry and router diagnostics (lmeyer@redhat.com)
- diagnostics: complete refactor (lmeyer@redhat.com)
- diagnostics: begin large refactor (deads@redhat.com)
- introduce `openshift ex diagnostics` (lmeyer@redhat.com)
- Only set masterIP with valid IPs, avoid calling OverrideConfig when writing
  config (jliggitt@redhat.com)
- refactored ldap utils (skuznets@redhat.com)
- Triggers should not be omit empty (ccoleman@redhat.com)
- If Vagrant sets a hostname that doesn't resolve it breaks containerized
  installs (bleanhar@redhat.com)
- enable extended test for old config (deads@redhat.com)
- Allow RequestHeaderIdentityProvider to redirect to UI login or challenging
  URL (jliggitt@redhat.com)
- Simplify messages (ccoleman@redhat.com)
- Update to etcd v2.1.2 (ccoleman@redhat.com)
- bump(github.com/coreos/etcd):v2.1.2 (ccoleman@redhat.com)
- Making the regex in hack/test-cmd.sh a little more flexible for downstream
  (bleanhar@redhat.com)
- Node IP can be passed as node config option (rpenta@redhat.com)
- Set console logo with css instead of within markup so that it can be
  customized. ref: https://github.com/openshift/origin/issues/4148
  (sgoodwin@redhat.com)
- Load UI extensions outside the OpenShift binary (spadgett@redhat.com)
- More UI integration test fixes (ffranz@redhat.com)
- Fix for issue #4437 - restarting the haproxy router still dispatches
  connections to a downed backend. (smitram@gmail.com)
- fix TestUnprivilegedNewProjectDenied flake (deads@redhat.com)
- bump(github.com/docker/spdystream):b2c3287 (ccoleman@redhat.com)
- make sure we don't accidentally drop admission plugins (deads@redhat.com)
- Allow origin clientcmd to use kubeconfig (ccoleman@redhat.com)
- Add project service, refactor projectNav (admin@benjaminapetersen.me)
- Disable complex console integration tests (ffranz@redhat.com)
- Do not print out the which error for etcd (ccoleman@redhat.com)
- Port Route to genericetcd (ccoleman@redhat.com)
- bump(github.com/openshift/openshift-sdn)
  4fc1cd198cd990b2c5120bd03304ef207b5ee1bc (rpenta@redhat.com)
- Reuse existing sdn GetNodeIP() for fetching node IP (rpenta@redhat.com)
- Make OsdnRegistryInterface compatible with openshift-sdn SubnetRegistry
  interface (rpenta@redhat.com)
- Make openshift SDN MTU configurable (rpenta@redhat.com)
- Fix nil panic (jliggitt@redhat.com)
- UPSTREAM: 13317: Recover panics in finishRequest, write correct API response
  (jliggitt@redhat.com)
- Make create flow forms always editable (spadgett@redhat.com)
- Bug 1256319: get: Fix nil timestamp output (mkargaki@redhat.com)
- Precompile Angular templates (spadgett@redhat.com)
- Revert "UPSTREAM: <carry>: implement a generic webhook storage"
  (ccoleman@redhat.com)
- Use a local webhook (ccoleman@redhat.com)
- Preserve permissions during image build copy (ccoleman@redhat.com)
- Add the kubernetes service IP to the cert list (ccoleman@redhat.com)
- Re-enable complex console integration tests (ffranz@redhat.com)
- ux for deleting a project, no api call implemented yet (gabe@ggruiz.me)
- Workaround slow ECDHE in F5 router tests (miciah.masters@gmail.com)
- fix typo in docker_version definition, handle origin pre-existing symlink
  (admiller@redhat.com)
- Convert zookeeper template to v1 (mfojtik@redhat.com)
- Skip second validation in when creating dockercfg secret (jhadvig@redhat.com)
- Fix bugz 1243529 - HAProxy template is overwritten by incoming changes.
  (smitram@gmail.com)
- Revert previous Vagrantfile cleanup (rpenta@redhat.com)
- Add empty state help for projects page (spadgett@redhat.com)
- F5 router implementation (miciah.masters@gmail.com)
- Add additional secrets to custom builds (cewong@redhat.com)
- stop: Add deprecation warning; redirect to delete (mkargaki@redhat.com)
- Remove unnecessary if condition in custom-docker-builder/buid.sh
  (nakayamakenjiro@gmail.com)
- Use os::build::setup_env when building extended test package
  (mfojtik@redhat.com)
- buildchain: Fix resource shortcut (mkargaki@redhat.com)
- oc new-app with no arguments will suggest --search and --list
  (jhadvig@redhat.com)
- bump(github.com/openshift/openshift-sdn)
  5a5c409df14c066f564b6015d474d1bf88da2424 (rpenta@redhat.com)
- Return node IPs in GetNodes() SDN interface (rpenta@redhat.com)
- bump(github.com/openshift/source-to-image)
  00d1cb3cb9224bb59c0a37bb2bdd0100e20e1982 (cewong@redhat.com)
- document why namespaces are stripped (bparees@redhat.com)
- Cleanup Vagrantfile (rpenta@redhat.com)
- rename jenkins version (bparees@redhat.com)
- add extended test for s2i incremental builds using docker auth credentials to
  push and pull (bparees@redhat.com)
- plugins/osdn: multitenant service isolation support (danw@redhat.com)
- Add ServiceNetwork field to ClusterNetwork struct (danw@redhat.com)
- bump(github.com/openshift/openshift-sdn):
  9d342eb61cfdcb1d77045ba69b27745f600385e3 (danw@redhat.com)
- Allow to override the default Jenkins image in example (mfojtik@redhat.com)
- Add support for dind image caching (marun@redhat.com)
- Improve graceful shutdown of dind daemon (marun@redhat.com)
- fix wf81 imagestream (bparees@redhat.com)
- Change default instance type (dmcphers@redhat.com)
- Fixup router test hostnames - good catch @Miciah (smitram@gmail.com)
- Restructure of nav layout and presentation at mobile resolutions to address
  https://github.com/openshift/origin/issues/3149 (sgoodwin@redhat.com)
- Add support for docker-in-docker dev cluster (marun@redhat.com)
- Prevent panic in import-image (ccoleman@redhat.com)
- Remove flakiness in webhook test (cewong@redhat.com)
- Add SOURCE_REF variable to builder container (mfojtik@redhat.com)
- change OpenShift references to Origin (pweil@redhat.com)
- Move documentation to test/extended/README.md (mfojtik@redhat.com)
- ext-tests: CLI interface docs (jhadvig@redhat.com)
- Initial docs about writing extended test (mfojtik@redhat.com)
- Remove sti-image-builder from our build-images flow (mfojtik@redhat.com)
- Add 'displayName' to Template (mfojtik@redhat.com)
- Fix 'pods "hello-openshift" cannot be updated' flake (jliggitt@redhat.com)
- make service targetPort consistent with container port (tangbixuan@gmail.com)
- Refactor vagrant provision scripts for reuse (marun@redhat.com)
- UPSTREAM: 13107: Fix portforward test flake with GOMAXPROCS > 1
  (jliggitt@redhat.com)
- UPSTREAM: 12162: Correctly error when all port forward binds fail
  (jliggitt@redhat.com)
- Minor cleanup (ironcladlou@gmail.com)
- Support prefixed deploymentConfig name (ironcladlou@gmail.com)
- Add vpc option to vagrantfile (dmcphers@redhat.com)
- Wait for the builder service account to get registry secrets in extended
  tests (mfojtik@redhat.com)
- Removing unused conversion tool, which was replaced with
  cmd/genconversion/conversion.go some time ago, already. (maszulik@redhat.com)
- Update k8s repository links and fix docs links (maszulik@redhat.com)
- reconcile-cluster-roles: Support union of default and modified cluster roles
  (mkargaki@redhat.com)
- Fix permission issues in zookeeper example (mfojtik@redhat.com)
- Make output directory symlinks relative links (stefw@redhat.com)
- Cleanup etcd install (ccoleman@redhat.com)
- Make config change triggers a default (ccoleman@redhat.com)
- Support generating DeploymentConfigs from run (ccoleman@redhat.com)
- UPSTREAM: 13011: Make run support other types (ccoleman@redhat.com)
- Add attach, run, and annotate to cli (ccoleman@redhat.com)
- Allow listen address to be overriden on api start (ccoleman@redhat.com)
- Completion generation can't run on Mac (ccoleman@redhat.com)
- Govet doesn't run on Mac (ccoleman@redhat.com)
- Split verify step into its own make task (ccoleman@redhat.com)
- Don't use _tmp or cp -u (ccoleman@redhat.com)
- Don't need to test same stuff twice (ccoleman@redhat.com)
- extended tests for setting forcePull in the 3 strategies; changes stemming
  from Ben's comments; some debug improvements; Michal's comments; address
  merge conflicts; adjust to extended test refactor (gmontero@redhat.com)
- Print line of error (ccoleman@redhat.com)
- Add stack dump to log on sigquit of sti builder (bparees@redhat.com)
- Overwriting a volume claim with --claim-name not working
  (ccoleman@redhat.com)
- change internal representation of rolebindings to use subjects
  (deads@redhat.com)
- remove export --all (deads@redhat.com)
- Tests failing at login, fix name of screenshots to be useful Remove the
  backporting of selenium since we no longer use phantom Remove phantomjs
  protractor config (jforrest@redhat.com)
- Remove double-enabled build controllers (jliggitt@redhat.com)
- add --all-namespaces to export (deads@redhat.com)
- fix --all (bparees@redhat.com)
- dump the namespaces at the end of e2e (bparees@redhat.com)
- Completion (ccoleman@redhat.com)
- OpenShift master setup example (ccoleman@redhat.com)
- Allow master-ip to set when running the IP directly (ccoleman@redhat.com)
- UPSTREAM: 12595 <drop>: Support status.podIP (ccoleman@redhat.com)
- Watch from the latest valid index for leader lease (ccoleman@redhat.com)
- add namespace to cluster SAR (deads@redhat.com)
- rpm: Added simple test case script for rpm builds. (smilner@redhat.com)
- Adding more retriable error types for push retry logic (jhadvig@redhat.com)
- Origin and Atomic OpenShift package refactoring (sdodson@redhat.com)
- Rename openshift.spec origin.spec (sdodson@redhat.com)
- update master for new recycler (mturansk@redhat.com)
- UPSTREAM: 5093+12603: adapt downward api volume to volume changes
  (deads@redhat.com)
- UPSTREAM: 6093+12603: adapt cephfs to volume changes (deads@redhat.com)
- UPSTREAM: 9870: configurable pv recyclers (deads@redhat.com)
- UPSTREAM: 12603: Expanded volume.Spec to full Volume and PV
  (deads@redhat.com)
- UPSTREAM: revert faab6cb: 9870: Allow Recyclers to be configurable
  (deads@redhat.com)
- disable SA secret ref limitting per SA (deads@redhat.com)
- Adding extended-tests for build-label (jhadvig@redhat.com)
- Add Docker labels (jhadvig@redhat.com)
- bump(openshift/source-to-image) a737bdd101de4a013758ad01f4bdd1c8d2f912b3
  (jhadvig@redhat.com)
- Extended test fixtures (jhadvig@redhat.com)
- Fix for issue #4035 - internally generated router keys are not unique.
  (smitram@gmail.com)
- Fix failing integration test expectation - we now return a service
  unavailable error rather than connect to 127.0.0.1:8080 (smitram@gmail.com)
- Include namespace in determining new-app dup objects (cewong@redhat.com)
- Use instance_type param (dmcphers@redhat.com)
- Remove default backend from the mix. In the first case, it returns incorrect
  info if something is serving on port 8080. The second bit is if nothing is
  running on port 8080, the cost to return a 503 is high. If someone wants
  custom 503 messages, they can always add a custom backend or use the
  errorfile 503 /path/to/page directive in a custom template.
  (smitram@gmail.com)
- UPSTREAM: 11827: allow permissive SA secret ref limitting (deads@redhat.com)
- Make the docker registry client loggable (ccoleman@redhat.com)
- bump(github.com/openshift/openshift-sdn):
  9dd0b510146571d42c5c9371b4054eae2dc5f82c (rpenta@redhat.com)
- Rename VindMap to VNIDMap (rpenta@redhat.com)
- Fixing the retry logic (jhadvig@redhat.com)
- Add standard vars to hook pod environment (ironcladlou@gmail.com)
- Make push retries more intelligent (jhadvig@redhat.com)
- Run e2e UI test in chrome (jliggitt@redhat.com)
- Remove dot imports from extended tests (mfojtik@redhat.com)
- display the host in 'oc status' (v.behar@free.fr)
- Typo in https proxy debug output (swapdisk@users.noreply.github.com)
- use push auth creds to pull previous image for incremental build
  (bparees@redhat.com)
- Fix sdn api field names to match openshift-sdn repo (rpenta@redhat.com)
- fixed -buildtags errors (skuznets@redhat.com)
- fixed -composites errors (skuznets@redhat.com)
- fixed -printf errors (skuznets@redhat.com)
- made verify-govet functional (skuznets@redhat.com)
- Bug 1247680 and 1251601 - new-app must validate --name instead of silently
  truncating and changing case (ffranz@redhat.com)
- Revert "Bug 1247680 - must not truncate svc names in the cli, rely on API
  validation" (ffranz@redhat.com)
- show build context in oc status (deads@redhat.com)
- make oc status build output consistent with deployments (deads@redhat.com)
- prevent kubectl/oc command drift (deads@redhat.com)
- Bug 1250676 - fixes --all-namespaces printer (ffranz@redhat.com)
- fixed printf errors (skuznets@redhat.com)
- enabled go tool -printf (skuznets@redhat.com)
- Add namespace flag to trigger enable instructions (ironcladlou@gmail.com)
- Add the DenyExecOnPrivileged admission control plugin to origin
  (cewong@redhat.com)
- make readme instructions work (deads@redhat.com)
- fixed method error (skuznets@redhat.com)
- added go tool vet -methods (skuznets@redhat.com)
- Move extended tests to separate Go packages (mfojtik@redhat.com)
- Replace FatalErr with ginkgos Fail (jhadvig@redhat.com)
- add jenkins to imagestream definitions (bparees@redhat.com)
- Reuse the previously evaulated 'sni' acl. (smitram@gmail.com)
- Add path based reencrypt routes - makes the map files sorting generic, was
  missing os_tcp_be.map and fixes a bug with wrong map used for reencrypt
  traffic and add integration tests. (smitram@gmail.com)
- Show last three builds by default in the UI (spadgett@redhat.com)
- Bug 1251845 - app name validation should require first char is a letter
  (jforrest@redhat.com)
- bump(go-ldap/ldap): c265aaa27b1c60c66f6d4695c6f33eb8b28989ad
  (jliggitt@redhat.com)
- Make UI treat bearer token type case-insensitively (jliggitt@redhat.com)
- Add persistent storage jenkins template (bparees@redhat.com)
- UPSTREAM: 8530: GCEPD mounting on Atomic (pweil@redhat.com)
- Set +e when removing (jhadvig@redhat.com)
- Bug 1250153 - console doesnt accept git ref in create from source URL
  (jforrest@redhat.com)
- Use ginkgo to run extended tests and use -focus to select which tests to run
  (mfojtik@redhat.com)
- UPSTREAM: 12221: Allow custom namespace creation in e2e framework
  (mfojtik@redhat.com)
- fix help typo (deads@redhat.com)
- bump(openshift/source-to-image) 2e52377338d425a290e74192ba8d53bb22965b0d
  (bparees@redhat.com)
- Add build number annotation and update UI pod template (spadgett@redhat.com)
- kill all child processes (jhadvig@redhat.com)
- Review feedback (ccoleman@redhat.com)
- Bug 1248464 - fixes message about builds created by new-app
  (ffranz@redhat.com)
- Bug 1247680 - must not truncate svc names in the cli, rely on API validation
  (ffranz@redhat.com)
- Add SCC checking to Source build controller strategy (cewong@redhat.com)
- Remove omitempty from server types (ccoleman@redhat.com)
- Refactor master start to split responsibilities (ccoleman@redhat.com)
- Support election of controllers (ccoleman@redhat.com)
- fix integration tests (deads@redhat.com)
- Bug 1253538 - webhook URLs should have a lower case type
  (jforrest@redhat.com)
- Leader lease utility (ccoleman@redhat.com)
- Add simple hello-world template to validate deployment of routes to pods
  (jcantril@redhat.com)
- bump(fsouza/go-dockerclient): 42d06e2b125654477366c320dcea99107a86e9c2
  (bparees@redhat.com)
- fixed composites errors (skuznets@redhat.com)
- added go tools vet -composites (skuznets@redhat.com)
- added openldap image artifacts (skuznets@redhat.com)
- do not register build storage if disabled (pweil@redhat.com)
- UPSTREAM:12675: don't swallow bad request errors (pweil@redhat.com)
- Ensure CLI OAuth client always has a single redirect_uri
  (jliggitt@redhat.com)
- bump(github.com/RangelReale/osin): c07b3bd1ee57089f63e6325c0ea035ceed2e905c
  (jliggitt@redhat.com)
- UPSTREAM: vjeantet/ldapserver: 15: fix ldapserver test panic
  (jliggitt@redhat.com)
- Disable CAdvisor insecure port (jliggitt@redhat.com)
- fix BuildConfign typo (bparees@users.noreply.github.com)
- changed integration test build tags (skuznets@redhat.com)
- enabled go tool vet -buildtags (skuznets@redhat.com)
- fixed unusedresult errors (skuznets@redhat.com)
- added go tool vet -unusedresult (skuznets@redhat.com)
- fixed structtags errors (skuznets@redhat.com)
- enabled go tool vet -structtags (skuznets@redhat.com)
- fixred unreachable errors (skuznets@redhat.com)
- added go tool vet -unreachable (skuznets@redhat.com)
- Allow API or controllers to start independently (ccoleman@redhat.com)
- Disable starting builds of a particular type when you don't have access
  (cewong@redhat.com)
- Add BuildConfig change trigger for initial build trigger (cewong@redhat.com)
- UPSTREAM: 12544: Re-add ServiceSpreadingPriority priority algorithm
  (jliggitt@redhat.com)
- Remove metadata from bindata assets (jliggitt@redhat.com)
- bump(jteeuwen/go-bindata): bfe36d3254337b7cc18024805dfab2106613abdf
  (jliggitt@redhat.com)
- Fix apiVersion in UI calls, re-enable project creation test
  (jliggitt@redhat.com)
- fix the preferred API order (deads@redhat.com)
- kube test artifact updates (deads@redhat.com)
- update to new testclient (deads@redhat.com)
- boring refactors (deads@redhat.com)
- UPSTREAM: 12669: make printer tolerate missing template flag
  (deads@redhat.com)
- UPSTREAM: 12498: Re-add timeouts for kubelet which is not in the upstream PR.
  (deads@redhat.com)
- UPSTREAM: 12602: expose e2e methods for downstream use (deads@redhat.com)
- UPSTREAM: 9009: Retry service account update when adding token reference
  (deads@redhat.com)
- UPSTREAM: 12552: only return name field (deads@redhat.com)
- UPSTREAM: 5093: adding downward api volume plugin (deads@redhat.com)
- UPSTREAM: 9844: EmptyDir volume SELinux support (deads@redhat.com)
- UPSTREAM: 9870: Allow Recyclers to be configurable (deads@redhat.com)
- UPSTREAM: 7893: scc allocation interface methods (deads@redhat.com)
- UPSTREAM: 6649: Add CephFS volume plugin (deads@redhat.com)
- UPSTREAM: 7893: scc (pweil@redhat.com)
- UPSTREAM: 8890: Allowing ActiveDeadlineSeconds to be updated for a pod
  (deads@redhat.com)
- UPSTREAM: <to-fix>: bind variable to flags, not just flagnames
  (deads@redhat.com)
- UPSTREAM: <drop>: add back flag types to reduce noise during this rebase
  (deads@redhat.com)
- UPSTREAM: <none>: search for mount binary in hostfs (ccoleman@redhat.com)
- UPSTREAM: <none>: Hack date-time format on *util.Time (ccoleman@redhat.com)
- UPSTREAM: <none>: Suppress aggressive output of warning (ccoleman@redhat.com)
- UPSTREAM: <carry>: update describer for dockercfg secrets (deads@redhat.com)
- UPSTREAM: <carry>: kube dep for tests (deads@redhat.com)
- UPSTREAM: <carry>: reallow the ability to post across namespaces in api
  (pweil@redhat.com)
- UPSTREAM: <carry>: support pointing oc exec to old openshift server
  (deads@redhat.com)
- UPSTREAM: <carry>: Add deprecated fields to migrate 1.0.0 k8s v1 data
  (jliggitt@redhat.com)
- UPSTREAM: <carry>: Allow pod start to be delayed in Kubelet
  (ccoleman@redhat.com)
- UPSTREAM: <carry>: Enable LimitSecretReferences in service account
  (jliggitt@redhat.com)
- UPSTREAM: <carry>: implement a generic webhook storage (ccoleman@redhat.com)
- UPSTREAM: <carry>: Disable UIs for Kubernetes and etcd (deads@redhat.com)
- UPSTREAM: <carry>: v1beta3 (deads@redhat.com)
- bump(github.com/prometheus/client_golang)
  692492e54b553a81013254cc1fba4b6dd76fad30 (deads@redhat.com)
- bump(github.com/spf13/cobra) 385fc87e4343efec233811d3d933509e8975d11a
  (deads@redhat.com)
- bump(github.com/fsouza/go-dockerclient)
  933433faa3e1c0bbc825b251143f8e77affbf797 (deads@redhat.com)
- bump(google.golang.org/api) 0c2979aeaa5b573e60d3ddffe5ce8dca8df309bd
  (deads@redhat.com)
- bump(k8s.io/kubernetes) 44c91b1a397e0580d403eb9e9cecd1dac3da0b25
  (deads@redhat.com)
- Disable create project in console integration tests (ffranz@redhat.com)
- Upgrade tag and import-image to be easier (ccoleman@redhat.com)
- Disable complex web console test scenarios until we can have clear runs
  (ffranz@redhat.com)
- added go vet to travis (skuznets@redhat.com)
- added go vet verification script (skuznets@redhat.com)
- Import and pull from v2 registries (ccoleman@redhat.com)
- accept --sa as argument for rolebinding (deads@redhat.com)
- add required value to parameter describer (bparees@redhat.com)
- allow regex test identifiers for docker int tests (skuznets@redhat.com)
- Rebuild assets (jliggitt@redhat.com)
- bump(github.com/jteeuwen/go-bindata):
  dce55d09e24ac40a6e725c8420902b86554f8046 (jliggitt@redhat.com)
- Refactor sorting by CreationTimestamp (rhcarvalho@gmail.com)
- do not remove output image when doing s2i build (bparees@redhat.com)
- Improve help on volumes and allow claim creation (ccoleman@redhat.com)
- Web console integration tests (contact@fabianofranz.com)
- rpm: Packages now generate configs when possible. (smilner@redhat.com)
- Trigger SDN node event when node ip changes (rpenta@redhat.com)
- bump openshift-sdn/ovssubnet(b4d90f205160ccf4a6e9c662f1b4568a6ac243f5)
  (rpenta@redhat.com)
- Prevent ipv6 bind for unsupported endpoints (ccoleman@redhat.com)
- Adapt flagtypes.Addr to support ipv6 hosts (ccoleman@redhat.com)
- Allow the bind address to be configured (ccoleman@redhat.com)
- add required field to sample templates (bparees@redhat.com)
- UPSTREAM: 211: Allow listen only ipv4 (ccoleman@redhat.com)
- rpm: added new bin files to ovs sections. (smilner@redhat.com)
- bump(github.com/openshift/source-to-image)
  c33ec325ac5b136e02cb999893aae0bdec4292ac (cewong@redhat.com)
- Add fake factory (mkargaki@redhat.com)
- Extended tested endpoints (miminar@redhat.com)
- refactored test to use upstream method (skuznets@redhat.com)
- fix package names for conversion generators (deads@redhat.com)
- UPSTREAM: <drop>: handle kube package refactor (deads@redhat.com)
- handle kube package refactors (deads@redhat.com)
- Add port table to browse services page (spadgett@redhat.com)
- More polishment for integration test (miminar@redhat.com)
- Inline test cases (miminar@redhat.com)
- Godoced exported method (miminar@redhat.com)
- Test improvements (miminar@redhat.com)
- fix remove-users help (deads@redhat.com)
- Added integration test for disabling web console (miminar@redhat.com)
- add layout.attrs to web console (admin@benjaminapetersen.me)
- update comments to accurately reflect validation (pweil@redhat.com)
- UPSTREAM: 12498: Re-add timeouts for kubelet which is not in the upstream PR.
  (pweil@redhat.com)
- Use skydns metrics (ccoleman@redhat.com)
- UPSTREAM: 219: External metrics registration (ccoleman@redhat.com)
- Gitserver should use DNS name for connecting to master (ccoleman@redhat.com)
- Change /etc to %%{_sysconfdir}. (avagarwa@redhat.com)
- update HACKING.md (skuznets@redhat.com)
- Change router to use host networking - adds a new --host-network option (the
  default). Setting it to false makes it use the container network stack.
  (smitram@gmail.com)
- output external serialization for router/registry (deads@redhat.com)
- Deny access to Web Console (miminar@redhat.com)
- UPSTREAM: search for mount binary in hostfs (ccoleman@redhat.com)
- refactors for review (pweil@redhat.com)
- non-interesting refactors (pweil@redhat.com)
- add group commands (deads@redhat.com)
- Add commas between pod template ports in UI (spadgett@redhat.com)
- Support auth in the gitserver (ccoleman@redhat.com)
- UPSTREAM:<carry>:kube dep for tests (pweil@redhat.com)
- UPSTREAM:<carry>:reallow the ability to post across namespaces in api
  installer (pweil@redhat.com)
- UPSTREAM:12271:expose codec in storage (pweil@redhat.com)
- UPSTREAM: 10636: Split kubelet server initialization for easier reuse
  (pweil@redhat.com)
- UPSTREAM: 9844: EmptyDir volume SELinux support (pmorie@gmail.com)
- UPSTREAM: carry: support pointing oc exec to old openshift server
  (deads@redhat.com)
- UPSTREAM: <carry>: Add deprecated fields to migrate 1.0.0 k8s v1 data
  (jliggitt@redhat.com)
- UPSTREAM: 9009: Retry service account update when adding token reference
  (deads@redhat.com)
- UPSTREAM: 5093: adding downward api volume plugin (salvatore-
  dario.minonne@amadeus.com)
- UPSTREAM: 8890: Allowing ActiveDeadlineSeconds to be updated for a pod
  (abhgupta@redhat.com)
- UPSTREAM: 6649: Add CephFS volume plugin (deads@redhat.com)
- UPSTREAM: <carry>: Enable LimitSecretReferences in service account admission
  (jliggitt@redhat.com)
- UPSTREAM: <none>: Suppress aggressive output of warning (ccoleman@redhat.com)
- UPSTREAM: <none>: Hack date-time format on *util.Time (ccoleman@redhat.com)
- UPSTREAM: <carry>: Disable UIs for Kubernetes and etcd (ccoleman@redhat.com)
- UPSTREAM: 9321: update describer for dockercfg secrets (deads@redhat.com)
- UPSTREAM: <carry>: Allow pod start to be delayed in Kubelet
  (ccoleman@redhat.com)
- UPSTREAM: 9870: Allow Recyclers to be configurable (deads@redhat.com)
- UPSTREAM: 7893: scc allocation interface methods (deads@redhat.com)
- UPSTREAM: <carry>: implement a generic webhook storage (ccoleman@redhat.com)
- UPSTREAM: 8607: service account groups (deads@redhat.com)
- UPSTREAM: 9472: expose name validation method (deads@redhat.com)
- UPSTREAM:<carry>: v1beta3 (pweil@redhat.com)
- UPSTREAM:7893: scc (pweil@redhat.com)
- bump(github.com/GoogleCloudPlatform/kubernetes):b73c53c37d06bc246eb862a83df51
  c8fd75994f8 (pweil@redhat.com)
- Allow subjectaccessreview to be invoked for a token (ccoleman@redhat.com)
- Newlines should be between warnings and output (ccoleman@redhat.com)
- Split hack/test-cmd.sh into individual tests (ccoleman@redhat.com)
- Add completions (ccoleman@redhat.com)
- Add a -q option for project to print the name (ccoleman@redhat.com)
- readlink -f doesn't work on Mac, fix tests (ccoleman@redhat.com)
- Remove unused constant variables (nakayamakenjiro@gmail.com)
- Fix silly error in example in test-integration.sh (pmorie@gmail.com)
- Update UI to oapi/v1 (spadgett@redhat.com)
- Update UI to k8s API version v1 (spadgett@redhat.com)
- Simplify error message improving responsiveness (rhcarvalho@gmail.com)
- Tweak test-integration.sh pipeline and add examples (pmorie@gmail.com)
- Extended MasterConfig for feature flags (miminar@redhat.com)
- Recognize atomic-enterprise binary namu (miminar@redhat.com)
- Make /token/display less like an API, send CLI redirect to informational page
  (jliggitt@redhat.com)
- Update documentation for new --host-network option. (smitram@gmail.com)
- Update build-chain examples to match product docs (adellape@redhat.com)
- LDAP group sync proposal (skuznets@redhat.com)
- descriptions for netnamespace objects (rchopra@redhat.com)
- multitenant sdn support; bump openshift-
  sdn/ovssubnet(74738c359b670c6e12435c1af10ee2802a4b0b64) vagrant instance
  updated to consume 2G (rchopra@redhat.com)
- add entrypoint for extended test (deads@redhat.com)
- Revert hack/test-cmd.sh changes from #3732 (ccoleman@redhat.com)
- Remove unnecessary godep requirement in extended tests
  (nagy.martin@gmail.com)
- Update hello-openshift example's README (nakayamakenjiro@gmail.com)
- remove 'experimental' from v1 log output (deads@redhat.com)
- support update on project (deads@redhat.com)
- rpm: Link /etc/openshift to /etc/origin if it exists. (smilner@redhat.com)
- Fix integration tests (mfojtik@redhat.com)
- Making test DRYer (jhadvig@redhat.com)
- Allow empty template parameters that can be generated (spadgett@redhat.com)
- sort edge map file (pweil@redhat.com)
- rpm: Using _unitdir instead of _prefix and path. (smilner@redhat.com)
- rpm: atomic-enterprise bash completion now generated. (smilner@redhat.com)
- rpm: Config location now /etc/origin/ (smilner@redhat.com)
- rpm: Now building AEP packages. (smilner@redhat.com)
- Refactor hack/test-extended to allow grouping (mfojtik@redhat.com)
- Refactor extended tests to use upstream e2e framework (mfojtik@redhat.com)
- Add openshift CLI testing framework (mfojtik@redhat.com)
- UPSTREAM: 12221: Allow custom namespace creation in e2e framework
  (mfojtik@redhat.com)
- bump(github.com/GoogleCloudPlatform/kubernetes/test/e2e)
  cd821444dcf3e1e237b5f3579721440624c9c4fa (mfojtik@redhat.com)
- bump(github.com/onsi/ginkgo) d981d36e9884231afa909627b9c275e4ba678f90
  (mfojtik@redhat.com)
- Fix 'oc' command to allow redirection of stdout (mfojtik@redhat.com)
- Enforce required on template parameters in UI (spadgett@redhat.com)
- prevent nil panic (deads@redhat.com)
- honor new group resources in authorizer (deads@redhat.com)
- handle cache.Index updates (deads@redhat.com)
- UPSTREAM: 11925: support multiple index values for a single object
  (deads@redhat.com)
- UPSTREAM: 11171: Added ability to list index keys (deads@redhat.com)
- merge AE docs work to OS (pweil@redhat.com)
- Allow additional image stream build triggers on BuildConfig
  (cewong@redhat.com)
- Add dns prefixes to default cert (jliggitt@redhat.com)
- Sort printed builds according to creation timestamp (nagy.martin@gmail.com)
- add required field to parameters (bparees@redhat.com)
- Generate the same labels in the UI as the CLI (spadgett@redhat.com)
- update to allow /api and /api/ for negotiation (deads@redhat.com)
- minor doc updates trying to run through README; comments from Ben
  (gmontero@redhat.com)
- routing.md update for router service account (pweil@redhat.com)
- return if SCCs can't be listed (pweil@redhat.com)
- add router service account requirements (pweil@redhat.com)
- bump(github.com/openshift/source-to-image)
  cfd95f2873bf687fbd2a4f32721462200d1b704a (bparees@redhat.com)
- Minor fixes (dmcphers@redhat.com)
- Minor tweak to hack/install-assets.sh for the RHEL AMI (bleanhar@redhat.com)
- shorted SAR response (deads@redhat.com)
- oc new-app --list (contact@fabianofranz.com)
- Add rolling update strategy for router with -10%% update percentage - fixes
  issue #3861 (smitram@gmail.com)
- customForcePull:  update swagger spec (gmontero@redhat.com)
- changes from update-generated-deep-copies.sh (gmontero@redhat.com)
- customForcePull:  changes to allow force pull of customer build strategy,
  including updates based on review with Ben; address gofmt issues
  (gmontero@redhat.com)
- Special case upstream kubernetes api package unit tests (pmorie@gmail.com)
- fix gendocs (deads@redhat.com)
- Added verification script for Swagger API object descriptions
  (skuznets@redhat.com)
- fail a build if there are no container statuses in the build pod
  (bparees@redhat.com)
- Add TLS support to docker client (cewong@redhat.com)
- Add mode http - fixes issue #3926. Add similar checks to the sni code path
  for specific path based lookups before using the host header lookup (in
  os_edge_http_be.map). (smitram@gmail.com)
- UPSTREAM: 9844: EmptyDir volume SELinux support (pmorie@gmail.com)
- UPSTREAM: 9384: Make emptyDir volumes work for non-root UIDs
  (pmorie@gmail.com)
- UPSTREAM: 9844: revert origin e53e78f: Support emptyDir volumes for
  containers running as uid != 0 (pmorie@gmail.com)
- UPSTREAM: 9384: revert origin 4e5cebd: EmptyDir volumes for non-root 2/2
  (pmorie@gmail.com)
- UPSTREAM: 9384: revert origin b92d1c7: Handle SecurityContext correctly for
  emptyDir volumes (pmorie@gmail.com)
- UPSTREAM: 9844: revert origin 73b2454: fix emptyDir idempotency bug
  (pmorie@gmail.com)
- UPSTREAM: 9384: revert origin 2d83001: Make emptyDir work when SELinux is
  disabled (pmorie@gmail.com)
- UPSTREAM: 9384: revert origin ac5f35b: Increase clarity in empty_dir volume
  plugin (pmorie@gmail.com)
- UPSTREAM: 9384: revert origin 6e57b2d: Make empty_dir unit tests work with
  SELinux disabled (pmorie@gmail.com)
- export: Initialize map for image stream tags
  (kargakis@users.noreply.github.com)
- add Group kind (deads@redhat.com)
- add cli display coverage tests (deads@redhat.com)
- issue3894: update vagrant sections of contributing and readme doc to account
  for recent tweaks in runtime (gmontero@redhat.com)
- test-cmd.sh broken on Mac (ccoleman@redhat.com)
- Generated docs (ccoleman@redhat.com)
- Make naming less specific to OpenShift (ccoleman@redhat.com)
- buildchain: Refactor to use the graph library
  (kargakis@users.noreply.github.com)
- Updated update scripts to allow for a settable output directory
  (skuznets@redhat.com)
- Newapp: fix image stream name used in deployment trigger (cewong@redhat.com)
- Cleanup deployment describe slightly (ccoleman@redhat.com)
- Add app=<name> label to new-app groups (ccoleman@redhat.com)
- Release tar should contain smaller oc (ccoleman@redhat.com)
- UPSTREAM: 11766: make kubelet prefer ipv4 address if available
  (deads@redhat.com)
- Remove gographviz (kargakis@users.noreply.github.com)
- UPSTREAM: 9384: Make empty_dir unit tests work with SELinux disabled
  (pmorie@gmail.com)
- render graph using DOT (deads@redhat.com)
- Include list of recent builds in error message (rhcarvalho@gmail.com)
- clean up handling of no output builds (bparees@redhat.com)
- UPSTREAM: 11303: Add CA data to service account tokens if missing or
  different (jliggitt@redhat.com)
- Make 'make check' run the kubernetes unit tests (pmorie@gmail.com)
- Add information about copying kubernetes artifacts in to HACKING.md
  (pmorie@gmail.com)
- UPSTREAM: add dependencies for packages missing for upstream unit tests
  (pmorie@gmail.com)
- Add third party deps stub (pmorie@gmail.com)
- UPSTREAM: 11147: Fix TestRunExposeService (pmorie@gmail.com)
- Add upstream examples, README files, etc (pmorie@gmail.com)
- Add copy-kube-artifacts.sh script (pmorie@gmail.com)
- WIP: make hack/test-go.sh run upstream unit tests (pmorie@gmail.com)
- UPSTREAM: 11698: Make copy_test.go failures easier to debug
  (pmorie@gmail.com)
- Newapp: Use labels for deployment config and service selectors
  (cewong@redhat.com)
- reintroduce missing conversions for imagestream kind and lowercase build
  trigger types (bparees@redhat.com)
- UPSTREAM: 9009: Retry service account update when adding token reference
  (deads@redhat.com)
- UPSTREAM: revert da0a3d: 9009: Retry service account update when adding token
  reference (deads@redhat.com)
- Generated docs (ccoleman@redhat.com)
- update swagger spec to match (deads@redhat.com)
- Add Cache-Control header (spadgett@redhat.com)
- Update swagger spec (spadgett@redhat.com)
- fix colliding serial numbers in certs (deads@redhat.com)
- Update object-describer to v1.0.2 (jforrest@redhat.com)
- Move Build cancellation and Pod deletion logic to HandleBuild
  (nagy.martin@gmail.com)
- bump(github.com/openshift/source-to-image)
  587d0f0a63589436322ac2ba6e01abb2f98a8dae (cewong@redhat.com)
- Updated Swagger spec, added Swagger spec verification (skuznets@redhat.com)
- Add a 'rsh' command for simpler remote access (ccoleman@redhat.com)
- Fix incorrect ENV["VAGRANT_LIBVIRT_URI"] if statement which causes "Missing
  required arguments: libvirt_uri (ArgumentError)" (takayoshi@gmail.com)
- UPSTREAM: 11729: Make exec reusable (ccoleman@redhat.com)
- Print consistent output for oadm manage-node --list-pods (rpenta@redhat.com)
- oc volume will allow changing volume type in case of unabiguous mount-path
  (rpenta@redhat.com)
- UPSTREAM: <carry>: Correct v1 deep_copy_generated.go (pmorie@gmail.com)
- Fix for tito 0.6.0 (sdodson@redhat.com)
- add reconcile-cluster-roles command (deads@redhat.com)
- Customize the events table layout and styles for better readability on mobile
  devices. (sgoodwin@redhat.com)
- UPSTREAM: 11669: add non root marker to sc types (pweil@redhat.com)
- OS: validation of host network and host ports in the SCC. (pweil@redhat.com)
- handle kube resources in project request template (deads@redhat.com)
- Bug 1245455 - fixes duplicated search results with openshift namespace
  (contact@fabianofranz.com)
- Bug 1245447 - fixes template search (contact@fabianofranz.com)
- use env var for config arg value (pweil@redhat.com)
- Rolling updater enhancements (ironcladlou@gmail.com)
- output invalid config field name (deads@redhat.com)
- UPSTREAM: 7893: validation of host network and host ports in the SCC.
  (pweil@redhat.com)
- New-app: set name of image stream with --name argument (cewong@redhat.com)
- don't fail status on forbidden lists (deads@redhat.com)
- update forbidden error to include structured kind (deads@redhat.com)
- Adding kubectl symlink for atomic host compatibility (bleanhar@redhat.com)
- Diff whole template for deployment config changes (ironcladlou@gmail.com)
- add tls termination type to printer and describer (pweil@redhat.com)
- Add "Show older builds" link to browse builds (spadgett@redhat.com)
- new-app search/list (contact@fabianofranz.com)
- make oc status output describeable (deads@redhat.com)
- Stop adding user to 'docker' group (marun@redhat.com)
- Vagrant: Allow override of IP addresses (marun@redhat.com)
- Allow registry client to work with registries that don't implement
  repo/tag/[tag] (cewong@redhat.com)
- Vagrant: Config synced folder type for devcluster (marun@redhat.com)
- Remove unused env vars from provision-config.sh (marun@redhat.com)
- do not use vagrant shared dir for volumes (pweil@redhat.com)
- do not use vagrant shared dir for volumes (pweil@redhat.com)
- Don't handle errors for dcs on retry failures
  (kargakis@users.noreply.github.com)
- add revision info to build descriptions (bparees@redhat.com)
- make fake client thread-safe (deads@redhat.com)
- UPSTREAM: 11597: make fake client thread-safe (deads@redhat.com)
- Refine canary text a bit more (ccoleman@redhat.com)
- Line up breadcrumbs and content on create from template page
  (spadgett@redhat.com)
- UPSTREAM: 10062: Rolling updater enhancements (ironcladlou@gmail.com)
- UPSTREAM: 10062: revert origin 316c2e84783fdb93450865eb8801f9d4dbe1f79c:
  support acceptance check in rolling updater (ironcladlou@gmail.com)
- Defer to Kubernetes factory where appropriate
  (kargakis@users.noreply.github.com)
- add dueling rc warning (deads@redhat.com)
- add graph markers (deads@redhat.com)
- Show more detail on browse image streams page (spadgett@redhat.com)
- expose: Default to the service generator when not exposing services
  (kargakis@users.noreply.github.com)
- Minor fixes to deployment README (rhcarvalho@gmail.com)
- Add canary doc (ccoleman@redhat.com)
- Deployment examples (ccoleman@redhat.com)
- Route should default to name, not serviceName (ccoleman@redhat.com)
- Fix nodeSelector enforcement by the kubelet (jliggitt@redhat.com)
- Fix errors creating from source in UI (spadgett@redhat.com)
- UPSTREAM: 10647 (carry until 10656): increase Kubelet timeouts to 1 hour
  (agoldste@redhat.com)
- Remove generated name from container ports (jliggitt@redhat.com)
- status: Warn for circular deps in buildConfigs
  (kargakis@users.noreply.github.com)
- cluster groups proposal (deads@redhat.com)
- Handle unrecognized types in DataService.createList() (spadgett@redhat.com)
- Default DNS name should change (ccoleman@redhat.com)
- Remove 12MB from the oc binary (ccoleman@redhat.com)
- react to gonum/graph rebase (deads@redhat.com)
- bump(github.com/gonum/graph)bde6d0fbd9dec5a997e906611fe0364001364c41
  (deads@redhat.com)
- remove auto build triggering and make jenkins auto deploy work
  (bparees@redhat.com)
- always show markers is oc status (deads@redhat.com)
- oc exec upgrade.md (deads@redhat.com)
- examples/sample-app: Use the registry kubeconfig, not master
  (walters@verbum.org)
- Test resource builder file extensions (jliggitt@redhat.com)
- Duplicate serials were being handed out because objects were copied
  (ccoleman@redhat.com)
- Move NoNamespaceKeyFunc into origin (jliggitt@redhat.com)
- UPSTREAM: revert 6cc0c51: Ensure no namespace on create/update root scope
  types (jliggitt@redhat.com)
- Describe security in readme (ccoleman@redhat.com)
- UPSTREAM: carry: support pointing oc exec to old openshift server
  (deads@redhat.com)
- UPSTREAM: 11333: pass along status errors for upgrades (deads@redhat.com)
- Update oc logs examples and docs (kargakis@users.noreply.github.com)
- make claim name parameterized (bparees@redhat.com)
- UPSTREAM: 10866: don't check extension for single files (jliggitt@redhat.com)
- fix racy SAR test (deads@redhat.com)
- clean up jenkins example (bparees@redhat.com)
- Web Console: Handle docker and custom builder strategy in templates
  (spadgett@redhat.com)
- update policy for pods/exec (deads@redhat.com)
- allow multiple edges of different kinds between nodes (deads@redhat.com)
- [docs] group cli commands; add missing ones (tnguyen@redhat.com)
- Output emptyDir notice to standard error (nagy.martin@gmail.com)
- Fix command descriptions and alignment (ccoleman@redhat.com)
- Run hack/test-assets first and fail if error (ccoleman@redhat.com)
- Completion and doc updates (ccoleman@redhat.com)
- Refactor for printer/namespace changes (ccoleman@redhat.com)
- Update completions (ccoleman@redhat.com)
- Don't print subcommands info (ccoleman@redhat.com)
- Print the version of the master and node on start (ccoleman@redhat.com)
- Provide a way to get the exact IP used by the master (ccoleman@redhat.com)
- Use containerized builds (ccoleman@redhat.com)
- UPSTREAM: <carry>: Leave v1beta3 enabled for now (ccoleman@redhat.com)
- UPSTREAM: 10024: add originator to reflector logging (deads@redhat.com)
- UPSTREAM: 9384: Increase clarity in empty_dir volume plugin
  (pmorie@gmail.com)
- UPSTREAM: 9384: Fixes for empty_dir merge problem (pmorie@gmail.com)
- UPSTREAM: 10841: Default --ignore-not-found to true for delete --all
  (jliggitt@redhat.com)
- UPSTREAM: <carry>: Add deprecated fields to migrate 1.0.0 k8s v1 data
  (jliggitt@redhat.com)
- UPSTREAM: 9971: add imports for map conversion types (bparees@redhat.com)
- UPSTREAM: 9009: Retry service account update when adding token reference
  (deads@redhat.com)
- UPSTREAM: 5093: adding downward api volume plugin (salvatore-
  dario.minonne@amadeus.com)
- UPSTREAM: 8890: Allowing ActiveDeadlineSeconds to be updated for a pod
  (abhgupta@redhat.com)
- UPSTREAM: 6649: Add CephFS volume plugin (deads@redhat.com)
- UPSTREAM: 9976: search for mount binary in hostfs (ccoleman@redhat.com)
- UPSTREAM: 9976: nsenter path should be relative (ccoleman@redhat.com)
- UPSTREAM: 8530: GCEPD mounting on Atomic (deads@redhat.com)
- UPSTREAM: <carry>: Enable LimitSecretReferences in service account admission
  (jliggitt@redhat.com)
- UPSTREAM: <none>: Suppress aggressive output of warning (ccoleman@redhat.com)
- UPSTREAM: <none>: Hack date-time format on *util.Time (ccoleman@redhat.com)
- UPSTREAM: <carry>: Disable UIs for Kubernetes and etcd (ccoleman@redhat.com)
- UPSTREAM: 9844: fix emptyDir idempotency bug (deads@redhat.com)
- UPSTREAM: 9384: Handle SecurityContext correctly for emptyDir volumes
  (pmorie@gmail.com)
- UPSTREAM: 9384: Make emptyDir work when SELinux is disabled
  (pmorie@gmail.com)
- UPSTREAM: 9384: EmptyDir volumes for non-root 2/2 (deads@redhat.com)
- UPSTREAM: 9844: Support emptyDir volumes for containers running as uid != 0
  (deads@redhat.com)
- UPSTREAM: 9321: update describer for dockercfg secrets (deads@redhat.com)
- UPSTREAM: 9971: generated conversion updates (deads@redhat.com)
- UPSTREAM: 10636(extra): patch to fix kubelet startup (deads@redhat.com)
- UPSTREAM: <carry>: Allow pod start to be delayed in Kubelet
  (ccoleman@redhat.com)
- UPSTREAM: 10636: Split kubelet server initialization for easier reuse
  (deads@redhat.com)
- UPSTREAM: 10635: Cloud provider should return an error (deads@redhat.com)
- UPSTREAM: 9870: Allow Recyclers to be configurable (deads@redhat.com)
- UPSTREAM: 7893: scc allocation interface methods (deads@redhat.com)
- UPSTREAM: 10062: support acceptance check in rolling updater
  (deads@redhat.com)
- UPSTREAM: <carry>: implement a generic webhook storage (ccoleman@redhat.com)
- UPSTREAM: <carry>: Ensure no namespace on create/update root scope types
  (jliggitt@redhat.com)
- UPSTREAM: 8607: service account groups (deads@redhat.com)
- UPSTREAM: 9472: expose name validation method (deads@redhat.com)
- UPSTREAM: 7893: scc (deads@redhat.com)
- bump(github.com/GoogleCloudPlatform/kubernetes):v1.0.0 (ccoleman@redhat.com)
- issue2740: updates to debugging doc for SELinux intermittent label issue
  (gmontero@redhat.com)
- status to indicate resources with broken secret/SA refs (deads@redhat.com)
- add graph analysis helpers (deads@redhat.com)
- issue1875: make the force pull option configurable in the sti build strategy
  definition; various upstream documentation clarifications / enhancements;
  comments around reqs for coding/testing changes that run in the builder pod;
  fixes after merging (changes lost); incorporate comments from Ben
  (gmontero@redhat.com)
- display standalone rcs (deads@redhat.com)
- Split oc and gitserver into their own binaries (ccoleman@redhat.com)
- Fix help message for client-certificate (chmouel@redhat.com)
- show standalone pods that back services (deads@redhat.com)
- suggest oc status from new-app (deads@redhat.com)
- Group commands in oadm for ease of use (rpenta@redhat.com)
- fix mutex for projectstatus (deads@redhat.com)
- README for hacking CLI commands (contact@fabianofranz.com)
- Show command to load templates on "Add to Project" page (spadgett@redhat.com)
- deploy: --enable-triggers should be used alone
  (kargakis@users.noreply.github.com)
- Clarify policy command on all projects page (spadgett@redhat.com)
- Added test for external kube proxied watches (skuznets@redhat.com)
- Issue 3502 - removing label propagation to build pods in build controller.
  (maszulik@redhat.com)
- LDAP password authenticator (jliggitt@redhat.com)
- Add scala source detector (jatescher@gmail.com)
- show RCs for services in oc status (deads@redhat.com)
- bump(github.com/openshift/source-to-image)
  72ed2c7edc4c4e03d490716404a25a6b7a15c890 (cewong@redhat.com)
- Handle "" for service.spec.portalIP on overview page (spadgett@redhat.com)
- return api error for privilege escalation attempt (deads@redhat.com)
- parallel resource lists for status (deads@redhat.com)
- Defer closing resp.Body after issuing an HTTP request
  (kargakis@users.noreply.github.com)
- UPSTREAM: 10024: add originator to reflector logging (deads@redhat.com)
- bump(github.com/vjeantet/asn1-ber): 85041cd0f4769ebf4a5ae600b1e921e630d6aff0
  (jliggitt@redhat.com)
- bump(github.com/vjeantet/ldapserver):
  5700661e721f508db936af42597a254c4ea6aea4 (jliggitt@redhat.com)
- bump(gopkg.in/asn1-ber.v1): 9eae18c3681ae3d3c677ac2b80a8fe57de45fc09
  (jliggitt@redhat.com)
- bump(github.com/go-ldap/ldap): 83e65426fd1c06626e88aa8a085e5bfed0208e29
  (jliggitt@redhat.com)
- Simplify rollback arguments (ironcladlou@gmail.com)
- Added test cases for HandleBuildPodDeletion and HandleBuildDeletion methods
  in build controller. (maszulik@redhat.com)
- refactor internal build api to match v1 (bparees@redhat.com)
- Docker registry client: handle [registry]/[name] specs (cewong@redhat.com)
- scaler: Sync with upstream behavior (kargakis@users.noreply.github.com)
- add masterCA to SA token controller (deads@redhat.com)
- Update headers and breadcrumbs to match button text (spadgett@redhat.com)
- Set expanded property on ng-repeat child scope for tasks
  (spadgett@redhat.com)
- Expose oapi (jliggitt@redhat.com)
- Vagrantfile: enable running on remote libvirtd (lmeyer@redhat.com)
- Bug 1232177 - handle mutually exclusive flags on oc process
  (contact@fabianofranz.com)
- add kubectl patch (deads@redhat.com)
- Sync .jshint options between root .jshintrc & test/.jshintrc, then fix
  outstanding errors (admin@benjaminapetersen.me)
- indicate builds that can't push (deads@redhat.com)
- UPSTREAM: 9384: Increase clarity in empty_dir volume plugin
  (pmorie@gmail.com)
- Awkward text wrapping on overview page (jhadvig@redhat.com)
- UPSTREAM: 9384: Fixes for empty_dir merge problem (pmorie@gmail.com)
- Add link to dismiss builds from overview (spadgett@redhat.com)
- UPSTREAM: 10841: Default --ignore-not-found to true for delete --all
  (jliggitt@redhat.com)
- [RPMs] Add nfs-utils to openshift-node requires (sdodson@redhat.com)
- Add 1.0.0 k8s v1 compatibility test (jliggitt@redhat.com)
- UPSTREAM: Carry: Add deprecated fields to migrate 1.0.0 k8s v1 data
  (jliggitt@redhat.com)
- Fix confusing output when cancelling deployments (ironcladlou@gmail.com)
- Remove unused function in CatalogImagesController (spadgett@redhat.com)
- Remove selection highlighting when sidebar hidden (spadgett@redhat.com)
- Remove "There is no service" message from overview (spadgett@redhat.com)
- Updating sti-image-builder with latest s2i (maszulik@redhat.com)
- run e2e cleanup as system:admin (deads@redhat.com)
- bump(github.com/openshift/source-to-
  image):e28fc867a72a6f2d1cb9898e0ce47c70e26909eb (maszulik@redhat.com)
- Clean-up desired replicas annotation for a complete deployment
  (kargakis@users.noreply.github.com)
- UPSTREAM: 9971: add imports for map conversion types (bparees@redhat.com)
- UPSTREAM: 9009: Retry service account update when adding token reference
  (deads@redhat.com)
- UPSTREAM: 5093: adding downward api volume plugin (salvatore-
  dario.minonne@amadeus.com)
- UPSTREAM: 8890: Allowing ActiveDeadlineSeconds to be updated for a pod
  (abhgupta@redhat.com)
- Avoid flicker on overview page when scaling (spadgett@redhat.com)
- Cleaned CONTRIBUTING.adoc and added information about problems with vagrant's
  synced folders. (maszulik@redhat.com)
- Image pruning improvements (agoldste@redhat.com)
- make imagestreamtag usage consistent (deads@redhat.com)
- prevent skydns metrics panic (deads@redhat.com)
- DeepCopy in Scheme (deads@redhat.com)
- update conversion/deep-copy generator (deads@redhat.com)
- NewProxier port range (deads@redhat.com)
- swagger API changes (deads@redhat.com)
- boring refactors (deads@redhat.com)
- UPSTREAM: 6649: Add CephFS volume plugin (deads@redhat.com)
- UPSTREAM: search for mount binary in hostfs (ccoleman@redhat.com)
- UPSTREAM: nsenter path should be relative (ccoleman@redhat.com)
- UPSTREAM: Run had invalid arguments (ccoleman@redhat.com)
- UPSTREAM: 8530: GCEPD mounting on Atomic (deads@redhat.com)
- UPSTREAM: 10169: Work around for PDs stop mounting after a few hours issue
  (deads@redhat.com)
- UPSTREAM: Enable LimitSecretReferences in service account admission
  (jliggitt@redhat.com)
- UPSTREAM: Hack date-time format on *util.Time (ccoleman@redhat.com)
- UPSTREAM: Suppress aggressive output of warning (ccoleman@redhat.com)
- UPSTREAM: Disable UIs for Kubernetes and etcd (ccoleman@redhat.com)
- UPSTREAM: 9844: fix emptyDir idempotency bug (deads@redhat.com)
- UPSTREAM: MISSING PULL: Handle SecurityContext correctly for emptyDir volumes
  (pmorie@gmail.com)
- UPSTREAM: MISSING PULL: Make emptyDir work when SELinux is disabled
  (pmorie@gmail.com)
- UPSTREAM: 9384: EmptyDir volumes for non-root 2/2 (deads@redhat.com)
- UPSTREAM: 9844: Support emptyDir volumes for containers running as uid != 0
  (deads@redhat.com)
- UPSTREAM: kube: update describer for dockercfg secrets (deads@redhat.com)
- UPSTREAM: 9971: generated conversion updates (deads@redhat.com)
- UPSTREAM: patch to fix kubelet startup (deads@redhat.com)
- UPSTREAM: fix SCC printers (deads@redhat.com)
- UPSTREAM: Allow pod start to be delayed in Kubelet (ccoleman@redhat.com)
- UPSTREAM: 10636: Split kubelet server initialization for easier reuse
  (deads@redhat.com)
- UPSTREAM: 10635 Cloud provider should return an error (deads@redhat.com)
- UPSTREAM: 9870 Allow Recyclers to be configurable (deads@redhat.com)
- UPSTREAM: scc allocation interface methods (deads@redhat.com)
- UPSTREAM: 10062 support acceptance check in rolling updater
  (deads@redhat.com)
- UPSTREAM: implement a generic webhook storage (ccoleman@redhat.com)
- UPSTREAM: Ensure no namespace on create/update root scope types
  (jliggitt@redhat.com)
- UPSTREAM: 8607 service account groups (deads@redhat.com)
- UPSTREAM: kube: expose name validation method (deads@redhat.com)
- UPSTREAM: Make util.Empty public (ccoleman@redhat.com)
- UPSTREAM: 7893 scc (deads@redhat.com)
- UPSTREAM: 7893 scc design (deads@redhat.com)
- UPSTREAM: Add "Info" to go-restful ApiDecl (ccoleman@redhat.com)
- UPSTREAM: Handle missing resolv.conf (ccoleman@redhat.com)
- UPSTREAM: Disable systemd activation for DNS (ccoleman@redhat.com)
- bump(github.com/elazarl/go-bindata-
  assetfs):3dcc96556217539f50599357fb481ac0dc7439b9 (deads@redhat.com)
- bump(github.com/syndtr/gocapability/capability):8e4cdcb3c22b40d5e330ade0b68cb
  2e2a3cf6f98 (deads@redhat.com)
- bump(github.com/miekg/dns):c13058f493c3756207ced654dce2986e812f2bcf
  (deads@redhat.com)
- bump(github.com/spf13/pflag): 381cb823881391d5673cf2fc41e38feba8a8e49a
  (jliggitt@redhat.com)
- bump(github.com/spf13/cobra): a8f7f3dc25e03593330100563f6c392224221899
  (jliggitt@redhat.com)
- bump(github.com/GoogleCloudPlatform/kubernetes):96828f203c8d960bb7a5ad649d1f3
  8f77ae8910f (deads@redhat.com)
- edit: Default to notepad for Windows and env renaming
  (kargakis@users.noreply.github.com)
- describe: Use spec.replicas when describing a deployment
  (kargakis@users.noreply.github.com)
- oc volume fixes (rpenta@redhat.com)
- Clean up to status output for ports and messages (ccoleman@redhat.com)
- Fix database service name copy&paste mistake (nagy.martin@gmail.com)
- Change our example templates to use ReadWriteOnce access modes
  (nagy.martin@gmail.com)
- Update readme to indicate docker 1.7 is broken (ccoleman@redhat.com)
- Restore failed initial deployment events (ironcladlou@gmail.com)
- Give cap_sys_net_bind to openshift binary (ccoleman@redhat.com)
- Support quay.io by allowing cookies on connect (ccoleman@redhat.com)
- further doc corrections/clarifications based on exercising *-ex; update
  .gitignore for .project; incorporate Ben's suggestions and Clayton's
  clarifications; general minor cleanup; fix typo (gmontero@redhat.com)
- Stop defaulting to Recreate deployment strategy (jliggitt@redhat.com)
- Add EXPOSE to our public Dockerfile (ccoleman@redhat.com)
- Refactored the use of restful.Container.Handle() method (skuznets@redhat.com)
- Stop creating deployments with recreate strategy (jliggitt@redhat.com)
- sample that uses direct docker pullspec for builder image
  (bparees@redhat.com)
- Don't produce events when initial deployment fails (ironcladlou@gmail.com)
- refactor graph veneers (deads@redhat.com)
- Added healthz endpoint to OpenShift (steve.kuznetsov@gmail.com)
- deploy: Remove extra newline when describing deployments
  (kargakis@users.noreply.github.com)
- deploy: Better message (kargakis@users.noreply.github.com)
- Making build logs error msgs more clear (j.hadvig@gmail.com)
- new-app: Don't swallow error (kargakis@users.noreply.github.com)
- sample-app: Show real output from oadm registry
  (kargakis@users.noreply.github.com)
- Fix for https://github.com/openshift/origin/issues/3446 (sgoodwin@redhat.com)
- Look for deployer label when filtering pods on overview page
  (spadgett@redhat.com)
- make test-cmd RCs non-conflicting (deads@redhat.com)
- Remove ellipses from links and buttons (spadgett@redhat.com)
- Wrapped tile content on builds and pods pages into 2 column layout for better
  presentation by using available space Update UI screenshots for browse builds
  and pods pages (sgoodwin@redhat.com)
- Avoid warning icon flicker on browse deployments page (spadgett@redhat.com)
- Remove v1beta1 annotation/label mapping (ironcladlou@gmail.com)
- update host name section (pweil@redhat.com)
- Reorganized master code (steve.kuznetsov@gmail.com)
- Use relative URIs in create flow links (spadgett@redhat.com)
- filter the pods the build controller looks at (bparees@redhat.com)
- add graph testing helpers (deads@redhat.com)
- Tweak headings and add separator on create page (spadgett@redhat.com)
- Make \w special character in template expression behave like PCRE
  (mfojtik@redhat.com)
- Fix the example command to list the projects (misc@redhat.com)
- log event for invalid output error (bparees@redhat.com)
- Bug 1223252: UPSTREAM: label: Invalidate empty or invalid value labels
  (kargakis@users.noreply.github.com)
- MySQL/Wordpress on NFS PVs (mturansk@redhat.com)
- Introduces auto-generation of CLI documents (contact@fabianofranz.com)
- Show namespace on project settings page (spadgett@redhat.com)
- Newapp: expose multiple ports in generated services (cewong@redhat.com)
- Add API version and kind to POST request content (spadgett@redhat.com)
- Fix deployment scaling race in test-cmd.sh (ironcladlou@gmail.com)
- allow http proxy env variables to be set in privileged sti container
  (bparees@redhat.com)
- More robust websocket error handling (spadgett@redhat.com)
- Correct registry auth for pruning (agoldste@redhat.com)
- Add image pruning e2e test (agoldste@redhat.com)
- require required fields in build objects (deads@redhat.com)
- remove dead build etcd package (deads@redhat.com)
- Allow private network to be used locally (ccoleman@redhat.com)
- Adjust examples indentation (contact@fabianofranz.com)
- Adjust 'kubectl config' examples to 'oc config' (contact@fabianofranz.com)
- Updated bash completion files (contact@fabianofranz.com)
- UPSTREAM: fixes kubectl config set-credentials examples
  (contact@fabianofranz.com)
- Remove `width: 100%%` from tile class (spadgett@redhat.com)
- Remove some pointless deployment logging (ironcladlou@gmail.com)
- Issue 3391 - allow optional image output for custom builder.
  (maszulik@redhat.com)
- Use a predictable tempdir naming convention (ironcladlou@gmail.com)
- add pod and rc spec nodes (deads@redhat.com)
- update prune error message to mention --confirm (chmouel@enovance.com)
- Fix typos in the repo (rpenta@redhat.com)
- elminate internal json tags forever (deads@redhat.com)
- Added support for multiple roles in oc secrets add
  (steve.kuznetsov@gmail.com)
- Correct Docker image Config type (agoldste@redhat.com)
- add warning for missing security allocator (deads@redhat.com)
- Add verification of generated content to make test (jliggitt@redhat.com)
- Fixed routes from root (steve.kuznetsov@gmail.com)
- Deflake TestBasicGroupManipulation (jliggitt@redhat.com)
- Allow who-can to check cluster-level access (jliggitt@redhat.com)
- make conversions convert and validation validate (deads@redhat.com)
- Always do a canary check during deployment (ironcladlou@gmail.com)
- More e2e-docker fixes (agoldste@redhat.com)
- Prevent long unbroken words from extending outside tile boundaries
  (spadgett@redhat.com)
- Fix typo (rhcarvalho@gmail.com)
- wait for imagestreamtags before requesting them (deads@redhat.com)
- validate extended args in config (deads@redhat.com)
- Warn user when using EmptyDir volumes (nagy.martin@gmail.com)
- Add EmptyDir volumes for new-app containers (nagy.martin@gmail.com)
- Clean up residual volume mounts from e2e-docker (agoldste@redhat.com)
- Newapp: Allow Docker FROM in Dockerfile to point to an image stream or
  invalid image (cewong@redhat.com)
- Split java console into separate package (jliggitt@redhat.com)
- bump(github.com/elazarl/go-bindata-assetfs):
  3dcc96556217539f50599357fb481ac0dc7439b9 (jliggitt@redhat.com)
- Use correct images for test-cmd (agoldste@redhat.com)
- Use correct images for e2e-docker (agoldste@redhat.com)
- Fix volume dir label for e2e-docker (agoldste@redhat.com)
- split graph package (deads@redhat.com)
- Adding rhel7 based origin-base Dockerfile (j.hadvig@gmail.com)
- dockercfg secret controllers shouldn't fail on NotFound deletes
  (deads@redhat.com)
- Add control/flow diagram for new-app (cewong@redhat.com)
- Update bash autocompletions (jliggitt@redhat.com)
- bump(github.com/spf13/cobra): a8f7f3dc25e03593330100563f6c392224221899
  (jliggitt@redhat.com)
- bump(github.com/spf13/pflag): 381cb823881391d5673cf2fc41e38feba8a8e49a
  (jliggitt@redhat.com)
- Remove duplicated template (rhcarvalho@gmail.com)
- Fix README.md markdown formatting (rhcarvalho@gmail.com)
- Remove imagemin step from asset build (jliggitt@redhat.com)
- bump(github.com/openshift/source-to-
  image):358cdb59db90b920e90a5f9a952ef7a3e11df3ad (bparees@redhat.com)
- sti to s2i (bparees@redhat.com)
- Show namespace, verb, resource for 'oadm policy who-can' cmd
  (rpenta@redhat.com)
- 'oc volume' test cases and fixes (rpenta@redhat.com)
- Updated 'oc env' help message (rpenta@redhat.com)
- Add policy cache wait in build admission integration tests
  (jliggitt@redhat.com)
- Template and image catalog updates (spadgett@redhat.com)
- defend against new-project racers (deads@redhat.com)
- Remove error when tracking tag target isn't found (agoldste@redhat.com)
- New-app: Expose ports specified in source Dockerfile (cewong@redhat.com)
- Add asset failure debugging (jliggitt@redhat.com)
- Make emptyDir work when SELinux is disabled (pmorie@gmail.com)
- Not beta! (ccoleman@redhat.com)
- fixed bash error (mturansk@redhat.com)
- fixed typo in script name (mturansk@redhat.com)
- fixed plugin init (mturansk@redhat.com)
- Add descriptions to our core objects and fix typos (ccoleman@redhat.com)
- Filter builds by completion rather than creation time on overview page
  (spadgett@redhat.com)
- add test for old config compatibility (deads@redhat.com)
- only handleErr on last retry failure (bparees@redhat.com)
- Now at one dot oh (ccoleman@redhat.com)
- bump(github.com/openshift/openshift-
  sdn/ovssubnet):cdd9955dc602abe8ef2d934a3c39417375c486c6 (rchopra@redhat.com)
- UPSTREAM: Ensure service account does not exist before deleting added/updated
  tokens (jliggitt@redhat.com)
- UPSTREAM: Add logging for invalid JWT tokens (jliggitt@redhat.com)
- Make etcd example more resilient to failure (mfojtik@redhat.com)
- new-app: Don't set spec.tags in output streams
  (kargakis@users.noreply.github.com)
- Bug 1232694 - Make the secret volume for push/pull secrets unique
  (mfojtik@redhat.com)
- use cookies for sticky sessions on http based routes (pweil@redhat.com)
- bump(github.com/openshift/openshift-
  sdn/ovssubnet):2bf8606dd9e0d5c164464f896e2223431f4b5099 (rchopra@redhat.com)
- Minor fixup to profiling instructions (ccoleman@redhat.com)
- Chmod hack/release.sh (ccoleman@redhat.com)
- UPSTREAM: fix emptyDir idempotency bug (pmorie@gmail.com)
- DeepCopy for util.StringSet (ccoleman@redhat.com)
- UPSTREAM: Make util.Empty public (ccoleman@redhat.com)
- UPSTREAM: use api.Scheme.DeepCopy() (ccoleman@redhat.com)
- Update default hostnames in cert (jliggitt@redhat.com)
- changed Recycler config for OS and added custom script for scrubbing in
  origin image (mturansk@redhat.com)
- Remove cached docker client repo on error (agoldste@redhat.com)
- update secret commands to give usage errors (deads@redhat.com)
- eliminate extra policy casting (deads@redhat.com)
- make policy interfaces (deads@redhat.com)
- switch policy types to map to pointers (deads@redhat.com)
- Prevent local fragment from being sent to a remote server
  (jliggitt@redhat.com)
- Properly handle Dockerfile build with no newline at the end
  (cewong@redhat.com)
- Validate redirect_uri doesn't contain path traversals (jliggitt@redhat.com)
- Add documentation on how to profile OpenShift (ccoleman@redhat.com)
- UPSTREAM: Allow recyclers to be configurable (mturansk@redhat.com)
- Re-enable timeout of -1 (no timeout) (jliggitt@redhat.com)
- UPSTREAM: Handle SecurityContext correctly for emptyDir volumes
  (pmorie@gmail.com)
- UPSTREAM: add client field mappings for v1 (jliggitt@redhat.com)
- UPSTREAM: Validate port protocol case strictly (jliggitt@redhat.com)
- bump(github.com/openshift/openshift-
  sdn/ovssubnet):962bcbc2400f6e66e951e61ba259e81a6036f1a2 (rchopra@redhat.com)
- Use uppercase protocol when creating from source in Web Console
  (spadgett@redhat.com)
- allow some resources to be created while the namespace is terminating
  (deads@redhat.com)
- Newapp: preserve tag specified in image stream input (cewong@redhat.com)
- add buildUpdate validation to protect spec (deads@redhat.com)
- UPSTREAM: fix exec infinite loop (agoldste@redhat.com)
- Ensure we're importing everything necessary for fallback codepaths too
  (sdodson@redhat.com)
- Improve deployment strategy logging (ironcladlou@gmail.com)
- Set min-width on pod-template-block (spadgett@redhat.com)
- Update registry/router to use rolling deployments (jliggitt@redhat.com)
- Add admission controller for build strategy policy check (cewong@redhat.com)
- Add admission controller for build strategy policy check (cewong@redhat.com)
- Population tuning should be parameterizable (ccoleman@redhat.com)
- Utility class for word-break. Fix for
  https://github.com/openshift/origin/issues/2560 (sgoodwin@redhat.com)
- prevent panic in oc process error handling (deads@redhat.com)
- UPSTREAM Fix bug where network container could be torn down before other pods
  (decarr@redhat.com)
- Set cache control headers for protected requests (ccoleman@redhat.com)
- Update build and deployment config associations when filter changes
  (spadgett@redhat.com)
- add service account to ipfailover (pweil@redhat.com)
- Impose a high default QPS and rate limit (ccoleman@redhat.com)
- Show correct restart policy on browse pods page (spadgett@redhat.com)
- Fixed the message about image being pushed with authorization
  (maszulik@redhat.com)
- Set some timeout values explicitly to http.Transport
  (nakayamakenjiro@gmail.com)
- Set http.Transport to get proxy from environment (nakayamakenjiro@gmail.com)
- Fix syntax error in e2e (pmorie@gmail.com)
- Adding validatiions for deployment config LatestVersion  - LatestVersion
  cannot be negative  - LatestVersion cannot be decremented  - LatestVersion
  can be incremented by only 1 (abhgupta@redhat.com)
- Deflake TestServiceAccountAuthorization (jliggitt@redhat.com)
- Only challenge for errors that can be fixed by authorizing
  (jliggitt@redhat.com)
- Add registry auth tests, fix short-circuit (jliggitt@redhat.com)
- Clean up orphaned deployers and use pod watches (ironcladlou@gmail.com)
- Make base filename configurable for create-api-client-config
  (jliggitt@redhat.com)
- UPSTREAM Fix ReadinessProbe: seperate readiness and liveness in the code
  (bparees@redhat.com)
- make service name a parameter (bparees@redhat.com)
- fix new-app errors (deads@redhat.com)
- OpenShift CLI cmd for volumes (rpenta@redhat.com)
- Create a formal release script (ccoleman@redhat.com)
- Updates to address part of bug 1230483 (slewis@fusesource.com)
- Specify seperate icon for 'pending' state vs 'running' state Add browse
  screenshots for Ashesh (sgoodwin@redhat.com)
- Setting NodeSelector on deployer/hook pods (abhgupta@redhat.com)
- make a non-escalating policy resource group (deads@redhat.com)
- UPSTREAM Don't pretty print by default (decarr@redhat.com)
- Export command to template should let me provide template name
  (decarr@redhat.com)
- UPSTREAM: Add CephFS volume plugin (mturansk@redhat.com)
- feedback for nodes group, namespace name check and weights (pweil@redhat.com)
- Add routingConfig.subdomain to master config (jliggitt@redhat.com)
- Test the origin docker container (ccoleman@redhat.com)
- UPSTREAM: search for mount binary in hostfs (ccoleman@redhat.com)
- Update readme (ccoleman@redhat.com)
- doc: Sync with master (kargakis@users.noreply.github.com)
- Change system:openshift-client username to system:master
  (jliggitt@redhat.com)
- config: Use already existing path (kargakis@users.noreply.github.com)
- Make admission errors clearer (jliggitt@redhat.com)
- Simplify createProvidersFromConstraints, add non-mutating test
  (jliggitt@redhat.com)
- UPSTREAM Rate limit scheduler to bind pods burst qps (decarr@redhat.com)
- More updates to data population scripts (decarr@redhat.com)
- Add non-mutating test (jliggitt@redhat.com)
- UPSTREAM: Expand variables in containers' env, cmd, args (pmorie@gmail.com)
- Update readme (ccoleman@redhat.com)
- Don't show "Get Started" message when project has replication controllers
  (spadgett@redhat.com)
- scc admission (pweil@redhat.com)
- router as restricted uid (pweil@redhat.com)
- UPSTREAM: work with SC copy, error formatting, add GetSCCName to provider
  (pweil@redhat.com)
- Disable image triggers on rollback (ironcladlou@gmail.com)
- Initial scripts for data population (decarr@redhat.com)
- Added parsing for new secret sources to enable naming source keys.
  (steve.kuznetsov@gmail.com)
- Support a containerized node (ccoleman@redhat.com)
- Fix command help for expose service (cewong@redhat.com)
- Use stricter name validation creating from source repository
  (spadgett@redhat.com)
- UPSTREAM its bad to spawn a gofunc per quota with large number of quotas
  (decarr@redhat.com)
- UPSTREAM: add simple variable expansion (pmorie@gmail.com)
- UPSTREAM: nsenter path should be relative (ccoleman@redhat.com)
- Build fixes. (avagarwa@redhat.com)
- Newapp: Remove hard coded image names for code detection (cewong@redhat.com)
- UPSTREAM: Add omitempty to RBD/ISCSI volume sources (jliggitt@redhat.com)
- update db templates to use imagestreams in openshift project
  (bparees@redhat.com)
- Cleaning up deployments on failure  - The failed deployment is scaled to 0  -
  The last completed deployment is scaled back up  - The cleanup is done before
  updating the deployment status to Failed  - A failure to clean up results in
  a transient error that is retried indefinitely (abhgupta@redhat.com)
- Test for and fix invalid markup nesting (jliggitt@redhat.com)
- Show "no deployments" message on browse page consistently
  (spadgett@redhat.com)
- Display start time instead of IP when not present (ccoleman@redhat.com)
- Bug 1229642 - new-build generates ImageStreams along with BuildConfig when
  needed. (maszulik@redhat.com)
- Allow setting service account in oadm registry/router (jliggitt@redhat.com)
- UPSTREAM: validate service account name in pod.spec (jliggitt@redhat.com)
- UPSTREAM: EmptyDir volumes for non-root 2/2 (pmorie@gmail.com)
- Fix broken --filename for oc env cmd (rpenta@redhat.com)
- Add tooltips to values we elide in the Web Console (spadgett@redhat.com)
- UPSTREAM: Added stop channel to prevent thread leak from watch
  (mturansk@redhat.com)
- app: Add element around overview on project.html page (stefw@redhat.com)
- Record events for initial deployment failures (ironcladlou@gmail.com)
- Node was blocking rather than running in goroutine (ccoleman@redhat.com)
- change .config/openshift to .kube (deads@redhat.com)
- Image push/pull policy updates (agoldste@redhat.com)
- change OPENSHIFTCONFIG to KUBECONFIG (deads@redhat.com)
- Bug 1229555 - fix broken example in oc new-app (contact@fabianofranz.com)
- Fix application template double escaping (decarr@redhat.com)
- Added stop channel to watched pods to prevent thread leak
  (mturansk@redhat.com)
- Use line-height: 1.3 for component headers (spadgett@redhat.com)
- Correlate and retrieve deployments by label (ironcladlou@gmail.com)
- Expose upstream generators and fix kubectl help (ccoleman@redhat.com)
- Support push secrets in the custom builder (agoldste@redhat.com)
- Prevent invalid names in new-app (cewong@redhat.com)
- Add emptyDir volumes to database templates (nagy.martin@gmail.com)
- Component refs are not docker image refs (ccoleman@redhat.com)
- Update README with create flow improvements (ccoleman@redhat.com)
- UPSTREAM: Run had invalid arguments (ccoleman@redhat.com)
- UPSTREAM: kill namespace defaulting (deads@redhat.com)
- Make tests more explicit (jliggitt@redhat.com)
- fix accessReview integration tests (deads@redhat.com)
- Implement deployment canary and fixes (ironcladlou@gmail.com)
- Upstream: node restart should not restart docker; fix node registration in
  vagrant (rchopra@redhat.com)
- Use better link for web console doc (dmcphers@redhat.com)
- Fix spelling errors (dmcphers@redhat.com)
- UPSTREAM: Add Pod IP to pod describe (ccoleman@redhat.com)
- expose stats port based on config (pweil@redhat.com)
- Upstream: make docker bridge configuration more dynamic (sdodson@redhat.com)
- UPSTREAM: add debug output for client calls (deads@redhat.com)
- Bug 1230066 - fixes oc help to use public git repo (contact@fabianofranz.com)
- bump(github.com/google/cadvisor):0.15.0-4-ga36554f (ccoleman@redhat.com)
- update imagestream location for ga (bparees@redhat.com)
- Add .tag* to gitignore, files generated by atom ctag (sdodson@redhat.com)
- Update bash completion for osc/osadm -> oc/oadm (sdodson@redhat.com)
- UPSTREAM: rest_client logging is generating too many metrics
  (ccoleman@redhat.com)
- whoami should show the current token and context (ccoleman@redhat.com)
- Cert serial numbers must be unique per execution (ccoleman@redhat.com)
- * Implement input from review (jhonce@redhat.com)
- Update to openshift-jvm 1.0.19 (slewis@fusesource.com)
- Infrastructure - Add and call vm-provision-fixup.sh (jhonce@redhat.com)
- fixes to sample app related instructions (gmontero@redhat.com)
- Handle spec.tags where tag name has a dot (spadgett@redhat.com)
- Change error check from IsConflict to IsAlreadyExists (jliggitt@redhat.com)
- add attach secret command (deads@redhat.com)
- deploy: Fix example and usage message (kargakis@users.noreply.github.com)
- Update README for images (j.hadvig@gmail.com)
- new-app: Fix empty tag in logs (kargakis@users.noreply.github.com)
- UPSTREAM: Support emptydir volumes for containers running as non-root
  (pmorie@gmail.com)
- Deflake integration test for overwrite policy (ccoleman@redhat.com)
- Allow GOMAXPROCS to be customized for openshift (ccoleman@redhat.com)
- Add test case for parallel.Run (ccoleman@redhat.com)
- SDN should signal when it's ready for pods to run (ccoleman@redhat.com)
- UPSTREAM: Allow OSDN to signal ready (ccoleman@redhat.com)
- UPSTREAM: Allow pod start to be delayed in Kubelet (ccoleman@redhat.com)
- Parallelize cert creation and test integration (ccoleman@redhat.com)
- bump(github.com/coreos/go-etcd/etcd):4cceaf7283b76f27c4a732b20730dcdb61053bf5
  (ccoleman@redhat.com)
- fix bad custom template (bparees@redhat.com)
- better error message for invalid source uri in sample custom builder
  (bparees@redhat.com)
- 'oc tag': create target stream if not found (agoldste@redhat.com)
- Update e2e test for new get pod output (decarr@redhat.com)
- UPSTREAM Decrease columns and refactor get pods layout (decarr@redhat.com)
- Support insecure registries (cewong@redhat.com)
- Fix deployer log message (jliggitt@redhat.com)
- changed hard-coded time to flag coming from CLI (mturansk@redhat.com)
- Expand short isimage id refs (agoldste@redhat.com)
- UPSTREAM: Add available volumes to index when not present
  (mturansk@redhat.com)
- Added PVRecycler controller to master (mturansk@redhat.com)
- Updated example README (steve.kuznetsov@gmail.com)
- UPSTREAM: GCEPD mounting on Atomic (mturansk@redhat.com)
- Adding a "/ready" endpoint for OpenShift (steve.kuznetsov@gmail.com)
- storage unit test to confirm validation (deads@redhat.com)
- add validateUpdate for API types (deads@redhat.com)
- add secrets subcommand to osc (deads@redhat.com)
- Use service accounts for build controller, deployment controller, and
  replication controller (jliggitt@redhat.com)
- Add tag command (agoldste@redhat.com)
- UPSTREAM: Adds ISCSI to PV and fixes a nil pointer issue
  (mturansk@redhat.com)
- return valid http status objects on rest errors (bparees@redhat.com)
- UPSTREAM: Normalize and fix PV support across volumes (mturansk@redhat.com)
- Disable QPS for internal API client (jliggitt@redhat.com)
- UPSTREAM: Added PV support for NFS (mturansk@redhat.com)
- update validation to handle validation argument reordering (deads@redhat.com)
- Update openshift-object-describer to 1.0.1 (spadgett@redhat.com)
- UPSTREAM: PV Recycling support (mturansk@redhat.com)
- update: Remove disabled --patch example (kargakis@users.noreply.github.com)
- Allow all Kubernetes controller arguments to be configured
  (ccoleman@redhat.com)
- UPSTREAM: Kubelet should log events at V(3) (ccoleman@redhat.com)
- Bug 1229731 - Updating docker rpm dependency in the specfile
  (bleanhar@redhat.com)
- Add registry-url flag to prune images (agoldste@redhat.com)
- UPSTREAM: Improve signature consistency for ValidateObjectMetaUpdate
  (deads@redhat.com)
- Issue 2880 - allow debugging docker push command. (maszulik@redhat.com)
- remove imagerepository policy refs (deads@redhat.com)
- Update to openshift-jvm 1.0.18 (slewis@fusesource.com)
- UPSTREAM: kube: update describer for dockercfg secrets (deads@redhat.com)
- Don't mutate build.spec when creating build pod (jliggitt@redhat.com)
- check name validation (deads@redhat.com)
- UPSTREAM: kube: expose name validation method (deads@redhat.com)
- make build config and instantiate consistent rest strategy (deads@redhat.com)
- expose: Bump validation and default flag message to routes
  (kargakis@users.noreply.github.com)
- Mostly golinting (kargakis@users.noreply.github.com)
- Fix webhook URL generation in UI (jliggitt@redhat.com)
- add version specific imagestream tags (bparees@redhat.com)
- add a default SCC for the cluster (pweil@redhat.com)
- Fix typos in tooltips on create from source page (spadgett@redhat.com)
- Consider existing deployments correctly when creating a new deployment
  (abhgupta@redhat.com)
- Switch the default API to v1 (ccoleman@redhat.com)
- UPSTREAM: v1 Secrets/ServiceAccounts needed a conversion
  (ccoleman@redhat.com)
- UPSTREAM: Alter default Kubernetes API versions (ccoleman@redhat.com)
- Remove trailing periods from help (ccoleman@redhat.com)
- Add types command showing OpenShift concepts (ccoleman@redhat.com)
- bump(github.com/MakeNowJust/heredoc):1d91351acdc1cb2f2c995864674b754134b86ca7
  (ccoleman@redhat.com)
- Pod failed, pending, warning style updates along with several bug fixes,
  inclusion of meta tags, and removal of inline styles and unused classes.
  (sgoodwin@redhat.com)
- Add shortcuts for service accounts (ccoleman@redhat.com)
- osc describe is should show spec tags when status empty (ccoleman@redhat.com)
- Update bindata.go for modified hawtio-core-navigation 2.0.48
  (spadgett@redhat.com)
- return proper http status failures from get logs (bparees@redhat.com)
- lower log level of missing tag for image message (bparees@redhat.com)
- Deleting deployment hook pods after a deployment completes
  (abhgupta@redhat.com)
- Subcommands should not display additional commands (ccoleman@redhat.com)
- Improve consistency of build trigger types (rhcarvalho@gmail.com)
- Replace occurrences of Github -> GitHub (rhcarvalho@gmail.com)
- Fixed webhook URLs (maszulik@redhat.com)
- Update CONTRIBUTING.adoc (bchilds@redhat.com)
- allow stats user/port/password to be configured (pweil@redhat.com)
- UPSTREAM: Pass memory swap limit -1 by default (decarr@redhat.com)
- Add get endpoints permission to node role for glusterfs (jliggitt@redhat.com)
- Add an export command to oc (ccoleman@redhat.com)
- Add support for processing multiple templates (mfojtik@redhat.com)
- Fix message in extended tests fixture (mfojtik@redhat.com)
- Security Allocator is configurable (ccoleman@redhat.com)
- Implemented an interface to expose the PolicyCache List() and Get() methods
  for policies and bindings on project and cluster level to the project
  authorization cache. (steve.kuznetsov@gmail.com)
- Namespace all build secrets (mfojtik@redhat.com)
- Update `osc` to `oc` in Web Console help text (spadgett@redhat.com)
- updates for feedback (pweil@redhat.com)
- promote whoami to osc (deads@redhat.com)
- add api description unit test (deads@redhat.com)
- UPSTREAM: Remove CORS headers from pod proxy responses (cewong@redhat.com)
- New-app: fix message when language is not detected. (cewong@redhat.com)
- new-app: Fix detectSource test (kargakis@users.noreply.github.com)
- Add persistent volume claims to database example templates
  (nagy.martin@gmail.com)
- Fix time duration formatting in push retry (mfojtik@redhat.com)
- UPSTREAM: Disable --patch for kubectl update
  (kargakis@users.noreply.github.com)
- Add process from stdin to hack/test-cmd.sh (mfojtik@redhat.com)
- Support processing using standard input (mfojtik@redhat.com)
- UPSTREAM: adding downward api volume plugin (salvatore-
  dario.minonne@amadeus.com)
- Must not apply labels to nested objects (contact@fabianofranz.com)
- UPSTREAM: Split resource.AsVersionedObject (ccoleman@redhat.com)
- UPSTREAM: ToJSON must support support forcing a JSON syntax check
  (contact@fabianofranz.com)
- Allow more master options to be configurable (ccoleman@redhat.com)
- Refactor usage and help templates to better catch corner cases
  (ccoleman@redhat.com)
- Fix travis builds (ccoleman@redhat.com)
- Add binaries for find and tree to registry image (pmorie@gmail.com)
- build hello-pod statically (bparees@redhat.com)
- Handle watch window expirations in UI (jliggitt@redhat.com)
- Generated conversions and deep copies (ccoleman@redhat.com)
- Make verify-generated-(deep-copies|conversion).sh required
  (ccoleman@redhat.com)
- Enable deep copy and conversions in OpenShift (ccoleman@redhat.com)
- UPSTREAM: Improve deep copy to work with OpenShift (ccoleman@redhat.com)
- Move conversions out of init() and give them names (ccoleman@redhat.com)
- Group commands in osc for ease of use (ccoleman@redhat.com)
- Rename 'osc' to 'os' and 'osadm' to 'oadm' (ccoleman@redhat.com)
- Display current and desired replicas on overview page (spadgett@redhat.com)
- Image API cleanup (agoldste@redhat.com)
- never retry pod/build sync delete failures (bparees@redhat.com)
- Controllers should be able to be lazily started (ccoleman@redhat.com)
- Round trip service account correctly in buildconfig/build
  (jliggitt@redhat.com)
- UPSTREAM: Enable LimitSecretReferences in service account admission
  (jliggitt@redhat.com)
- Properly resolve tag of build.Output in conversion (ccoleman@redhat.com)
- Fixed the error from webhook when secret mismatch (maszulik@redhat.com)
- Minor master cleanups (ccoleman@redhat.com)
- Remove v1beta1 (ccoleman@redhat.com)
- Renamed --build flag to --strategy and fixed taking that flag into account
  even when repo has Dockerfile. (maszulik@redhat.com)
- Issue 2695 - new-build command creating just BuildConfig from provided source
  and/or image. (maszulik@redhat.com)
- have osc status highlight disabled deployment configs (deads@redhat.com)
- Too much logging from cert creation (ccoleman@redhat.com)
- Use deployer service account for deployments (jliggitt@redhat.com)
- UPSTREAM: process new service accounts (jliggitt@redhat.com)
- Differentiate nodes volumes directories (jhonce@redhat.com)
- ensure route exists under one service only (pweil@redhat.com)
- UPSTREAM: remove client facet from metrics (ccoleman@redhat.com)
- Show correct message on project settings when no display name
  (spadgett@redhat.com)
- UPSTREAM Insert 'svc' into the DNS search paths (decarr@redhat.com)
- add output for what remove-user is doing (deads@redhat.com)
- Fix typos in documentation (konzems@gmail.com)
- Fix vagrant setup so that minions are pre-registered; Update Godeps with
  latest openshift-sdn (rchopra@redhat.com)
- Fix image reference generation for deployment configs (cewong@redhat.com)
- Remove TaskList polling (jliggitt@redhat.com)
- Updates to create flow forms (spadgett@redhat.com)
- UPSTREAM: security context constraints (pweil@redhat.com)
- Ensure KubeletConfig's RootDirectory is correct (agoldste@redhat.com)
- Converted glog.Error() -> util.HandleError(errors.New()), glog.Errorf() ->
  util.HandleError(fmt.Errorf()) where code was eating the error.
  (steve.kuznetsov@gmail.com)
- disable kube v1beta1 and v1beta2 by default (deads@redhat.com)
- update docs to remove v1beta1 (deads@redhat.com)
- Don't default displayname/description to project name (jliggitt@redhat.com)
- Support template watch (jimmidyson@gmail.com)
- reaper: Exit tests as soon as actions lengths don't match
  (kargakis@users.noreply.github.com)
- README.md: Fix up the 'Start Developing' instructions (stefw@redhat.com)
- Update CONTRIBUTING.adoc (hyun.soo.kim1112@gmail.com)
- Don't import if a spec.tag is tracking another (agoldste@redhat.com)
- Expose _endpoints.<> as a DNS endpoint (ccoleman@redhat.com)
- Fixing console link and adding link to new api doc (dmcphers@redhat.com)
- do not bounce router for endpoint changes that do not change the data
  (pweil@redhat.com)
- Fixes to Contributing doc (dmcphers@redhat.com)
- Updated swagger doc (ccoleman@redhat.com)
- Add test for tracking tags when ISMs are posted (agoldste@redhat.com)
- Add 'osc import-image' command (agoldste@redhat.com)
- New-app: more helpful message when not generating a service
  (cewong@redhat.com)
- Update proxy URL path (slewis@fusesource.com)
- Fix new-app help for app-from-image (cewong@redhat.com)
- Add v1 descriptions to oauth (decarr@redhat.com)
- Fix device busy issues on serial e2e runs (pmorie@gmail.com)
- Fix CLI deployment cancellation (ironcladlou@gmail.com)
- Make deployment config reaper reentrant (ironcladlou@gmail.com)
- don't share volumes directory in vagrant (pweil@redhat.com)
- Allow overriding registry URL when image pruning (agoldste@redhat.com)
- Minor spec file fixes. (avagarwa@redhat.com)
- UPSTREAM: Fix proxying of URLs that end in "/" in the pod proxy
  (cewong@redhat.com)
- UPSTREAM: make getFromCache more tolerant (deads@redhat.com)
- Allow the kubelet to take the full set of params (ccoleman@redhat.com)
- Adding 'openshift.io/' namespace to 'displayName', 'description' annotations.
  Added annotations to api/types.go and updated references.
  (steve.kuznetsov@gmail.com)
- UPSTREAM: Support kubelet initialization in order (ccoleman@redhat.com)
- UPSTREAM Fix error in quantity code conversion (decarr@redhat.com)
- UPSTREAM Fix namespace controller to tolerate not found items
  (decarr@redhat.com)
- New-app: add support for template files (cewong@redhat.com)
- Revert SDN and Kubelet initialization ordering (sdodson@redhat.com)
- update origin-version-change for configapi.Config objects (deads@redhat.com)
- fix output messages for api versions (deads@redhat.com)
- Rename dry-run to confirm for prune commands (agoldste@redhat.com)
- sticky sessions (pweil@redhat.com)
- Actually remove router and registry from experimental commands
  (kargakis@users.noreply.github.com)
- UPSTREAM: Match the isDefaultRegistryMatch with upstream (mfojtik@redhat.com)
- expose: Allow specifying a hostname when generating routes
  (kargakis@users.noreply.github.com)
- expose: Fix service validation (kargakis@users.noreply.github.com)
- dcController: Use annotations to list deployments
  (kargakis@users.noreply.github.com)
- Make origin project delete controller more fault tolerant to stop O(n) minute
  deletes (decarr@redhat.com)
- Make default namespace and osadm new-project set up service account roles
  (jliggitt@redhat.com)
- Update e2e to handle registry auth (agoldste@redhat.com)
- Require token in client config for image pruning (agoldste@redhat.com)
- Image policy updates (agoldste@redhat.com)
- Update registry policy (agoldste@redhat.com)
- Allow registry /healthz without auth (agoldste@redhat.com)
- Enable registry authentication (agoldste@redhat.com)
- Remove username validation for registry login (agoldste@redhat.com)
- Delete deploymentConfig before reaping deployments (ironcladlou@gmail.com)
- fix reverted code (pweil@redhat.com)
- Fix incorrect Content-Type in some Web Console responses
  (spadgett@redhat.com)
- Add v1 descriptions to image api (decarr@redhat.com)
- update generated kubeconfig keys to match osc login (deads@redhat.com)
- Move registry and router out of experimental commands
  (kargakis@users.noreply.github.com)
- Relax source repository URL validation (spadgett@redhat.com)
- Updated validation for builds per @rhcarvalho comments in #2699: separated
  and hardened test cases and simplified validation for multiple ICTs
  (maszulik@redhat.com)
- Remove "image repositories" from example osc command (spadgett@redhat.com)
- Add v1 descriptions to user api (decarr@redhat.com)
- Add v1 descriptions to external template api (decarr@redhat.com)
- UPSTREAM: json marshalling error must manifest earlier in resource visitors
  (contact@fabianofranz.com)
- fix overwrite-policy prefix (deads@redhat.com)
- Add v1 descriptions to sdn api (decarr@redhat.com)
- Add v1 descriptions to route api (decarr@redhat.com)
- Add missing description to v1 project api (decarr@redhat.com)
- Project node selector fixes (rpenta@redhat.com)
- Don't reopen websockets closed by DataService.unwatch() (spadgett@redhat.com)
- Add v1 descriptions to all build fields (decarr@redhat.com)
- Bug 1224089: UPSTREAM: expose: Better error formatting and generic flag
  message (kargakis@users.noreply.github.com)
- Add descriptions to v1 policy api, remove deprecated field
  (decarr@redhat.com)
- stop: Reap all deployments of a config (kargakis@users.noreply.github.com)
- Update `osc logs` examples (rhcarvalho@gmail.com)
- Guard against null deployment config triggers (spadgett@redhat.com)
- Update hawtio-core-navigation to 2.0.48 (spadgett@redhat.com)
- Add commit to github links, improve git link display (jliggitt@redhat.com)
- Remove --node-selector from osc new-project (jliggitt@redhat.com)
- Add godoc for mcs.ParseRange (pmorie@gmail.com)
- Fix issue#2655; bz1225410; rebase openshift-sdn Godeps (rchopra@redhat.com)
- Switch UI to using legacy API prefix (jliggitt@redhat.com)
- fix grammar of resource create message (bparees@redhat.com)
- disable v1beta1 by default (deads@redhat.com)
- UPSTREAM: Backport schema output fixes (ccoleman@redhat.com)
- JSON examples migration to v1beta3 leftovers (maszulik@redhat.com)
- Make pod eviction timeout configurable (rpenta@redhat.com)
- Honor clicks anywhere inside a link (jliggitt@redhat.com)
- add tmp volume so scratch image will work (bparees@redhat.com)
- Allow populating bearer token from file contents (jliggitt@redhat.com)
- Issue 2586 - allow only one ImageChangeTrigger for BuildConfig.
  (maszulik@redhat.com)
- Generate swagger specs and docs for our API (ccoleman@redhat.com)
- Refactor deploy hook retry policy (ironcladlou@gmail.com)
- Tearing down old deployment before bringing up new one for the recreate
  strategy (abhgupta@redhat.com)
- Simplify the deploy trigger int test (ironcladlou@gmail.com)
- UPSTREAM: Add "Info" to go-restful ApiDecl (ccoleman@redhat.com)
- UPSTREAM: Hack date-time format on *util.Time (ccoleman@redhat.com)
- UPSTREAM: Expose OPTIONS but not TRACE (ccoleman@redhat.com)
- UPSTREAM: Patch needs a type for swagger doc (ccoleman@redhat.com)
- Properly support the 'oapi' prefix (ccoleman@redhat.com)
- Show template parameter descriptions on create page (spadgett@redhat.com)
- Restore comments and remove empty ServiceAccount (mfojtik@redhat.com)
- Migrate YAML files to v1beta3 (mfojtik@redhat.com)
- Fix hack/convert-samples to deal with YAML files (mfojtik@redhat.com)
- Follow-on Web Console fixes for osapi/v1beta3 (spadgett@redhat.com)
- Fix Cancel button error on Web Console create pages (spadgett@redhat.com)
- Add UI e2e tests (jliggitt@redhat.com)
- Rework dockercfg in builder package to use upstream keyring
  (mfojtik@redhat.com)
- expose: Fix service validation and help message
  (kargakis@users.noreply.github.com)
- Retry the output image push if failed (mfojtik@redhat.com)
- UPSTREAM: fix omitempty on service account in v1beta3 (jliggitt@redhat.com)
- Deleting deployer pods for failed deployment before retrying
  (abhgupta@redhat.com)
- Update Web Console to use osapi/v1beta3 (spadgett@redhat.com)
- Fixing doc to make clear where the source should be (scitronpousty@gmail.com)
- Updated code with latest S2I. (maszulik@redhat.com)
- bump(github.com/openshift/source-to-
  image):77e3b722b028b8af94a3606d0dbb76dc377755fd (maszulik@redhat.com)
- Added Lists to origin-version-changer (maszulik@redhat.com)
- fix long help description to remove garbage chars (decarr@redhat.com)
- Re-generate bash completions (contact@fabianofranz.com)
- Fixes bash completion gen script (contact@fabianofranz.com)
- validate lasttriggeredimageid hasn't changed before running build
  (bparees@redhat.com)
- create osc policy * for non-cluster admin usage (deads@redhat.com)
- make subcommands return non-zero status on failures (deads@redhat.com)
- Build ImageChangeController shouldn't return early if it encounters an
  Instantiate error (mfojtik@redhat.com)
- Adds steps for safely restarting iptables (mrunal@me.com)
- deployconfig requires kind (deads@redhat.com)
- Security allocator and repair logic (ccoleman@redhat.com)
- Create UID and MCS category allocators (ccoleman@redhat.com)
- UPSTREAM: Add contiguous allocator (ccoleman@redhat.com)
- UPSTREAM Force explicit namespace provision (decarr@redhat.com)
- UPSTREAM Do not set container requests in limit ranger for Kube 1.0
  (decarr@redhat.com)
- [RPMs]: Install bash completion files (sdodson@redhat.com)
- Make the TriggeredByImage field ObjectReference (mfojtik@redhat.com)
- UPSTREAM: kube: serialize dockercfg files with auth (deads@redhat.com)
- auto-generate dockercfg secrets for service accounts (deads@redhat.com)
- UPSTREAM: kube: cleanup unused service account tokens (deads@redhat.com)
- Print name of existing pods with deployer-pod names (pmorie@gmail.com)
- Fixed typo in BuildRequest field name (mfojtik@redhat.com)
- Replace custom/flaky pod comparison with DeepEqual (ironcladlou@gmail.com)
- Adding meaningful comments deployments cannot be started/retried
  (abhgupta@redhat.com)
- Added missing test object and updated DeploymentConfig's ImageChange trigger
  definition to match current validations. (maszulik@redhat.com)
- Guard against missing error details kind or ID (spadgett@redhat.com)
- Add example Git URL to Create page (spadgett@redhat.com)
- integration/dns_test.go: don't expect recursion (lmeyer@redhat.com)
- SkyDNS: don't recurse requests (lmeyer@redhat.com)
- UPSTREAM: Disable systemd activation for DNS (ccoleman@redhat.com)
- UPSTREAM: Handle missing resolv.conf (ccoleman@redhat.com)
- bump(github.com/skynetservices/skydns):01de2a7562896614c700547f131e240b665468
  0c (lmeyer@redhat.com)
- Show correct error details on browse builds page (spadgett@redhat.com)
- UPSTREAM: Show pods number when describing services
  (kargakis@users.noreply.github.com)
- Use kubectl constants for dc reaper interval/timeout
  (kargakis@users.noreply.github.com)
- Make node's Docker exec handler configurable (agoldste@redhat.com)
- Rename BuildRequest.Image to TriggedByImage (mfojtik@redhat.com)
- Support cancelling deployment hooks (etc) (ironcladlou@gmail.com)
- Add more description for the BuildRequest Image field (mfojtik@redhat.com)
- UPSTREAM: kube: add pull secrets to service accounts (deads@redhat.com)
- Rename osc resize to osc scale (kargakis@users.noreply.github.com)
- make api levels configuratable (deads@redhat.com)
- UPSTREAM: rename resize to scale (kargakis@users.noreply.github.com)
- Tolerate missing BuildStatusNew in webhookgithub integration test
  (mfojtik@redhat.com)
- Fix TestWebhookGithubPushWithImage integration test (mfojtik@redhat.com)
- Resolve ImageStream reference outside loop in resolveImageSecret
  (mfojtik@redhat.com)
- Do not mutate DefaultServiceAccountName in BuildGenerator
  (mfojtik@redhat.com)
- Fix build image change race (agoldste@redhat.com)
- Provide default PushSecret and PullSecret using Service Account
  (mfojtik@redhat.com)
- Auto-wire push secrets into builds (agoldste@redhat.com)
- UPSTREAM: Add 'docker.io' and 'index.docker.io' to default registry
  (mfojtik@redhat.com)
- Fix name collisions between build and deployment pods (cewong@redhat.com)
- Fix structure of webhooks URL display in web console (cewong@redhat.com)
- UPSTREAM: Allowing ActiveDeadlineSeconds to be updated for a pod
  (abhgupta@redhat.com)
- Bug 1220998 - improve message in osc env update errors
  (contact@fabianofranz.com)
- make registry and router exit non-zero for failures (deads@redhat.com)
- UPSTREAM: Add support for pluggable Docker exec handlers
  (agoldste@redhat.com)
- Ensure OpenShift content creation results in namespace finalizer
  (decarr@redhat.com)
- remove-from-project and integration tests (deads@redhat.com)
- Update README.md (hyun.soo.kim1112@gmail.com)
- Deployer pod failure detection improvements (ironcladlou@gmail.com)
- update readme - centos7 has docker 1.6 (matt@redhat.com)
- Fix pkg/template test to use stored JSON fixture (mfojtik@redhat.com)
- Set default BuildTriggerPolicy.ImageChange when not given
  (rhcarvalho@gmail.com)
- Bug 1224097: Don't use custom names for route.servicename
  (kargakis@users.noreply.github.com)
- UPSTREAM: expose: Use separate parameters for default and custom name
  (kargakis@users.noreply.github.com)
- Fix pkg/template tests to use v1beta3 (mfojtik@redhat.com)
- Migrate all JSON examples to v1beta3 (mfojtik@redhat.com)
- Add script which migrate all JSON samples to certain version
  (mfojtik@redhat.com)
- Removing unnecessary namespace prefix for deployment/deploymentConfig/Repo
  (j.hadvig@gmail.com)
- Add test to detect config changes (jliggitt@redhat.com)
- Fix flaky TestConcurrentBuild* tests (jliggitt@redhat.com)
- Add proxy examples to master and node sysconfig files (sdodson@redhat.com)
- Add eth1 to virtual box interfaces and add support to not watch/monitor port
  for the f5 ipfailover use case (--watch-port=0). (smitram@gmail.com)
- Don't default node selector for openshift admin manag-node cmd
  (rpenta@redhat.com)
- Refactor to match upstream (ccoleman@redhat.com)
- UPSTREAM: Add groups to service account JWT (jliggitt@redhat.com)
- UPSTREAM: print more useful error (ccoleman@redhat.com)
- UPSTREAM: implement a generic webhook storage (ccoleman@redhat.com)
- UPSTREAM: Suppress aggressive output of warning (ccoleman@redhat.com)
- UPSTREAM: Disable UIs for Kubernetes and etcd (ccoleman@redhat.com)
- bump(github.com/GoogleCloudPlatform/kubernetes):496be63c0078ce7323aede59005ad
  bd3e9eef8c7 (ccoleman@redhat.com)
- Refactor deployment cancellation handling (ironcladlou@gmail.com)
- Add breadcrumbs to pages in create flow (spadgett@redhat.com)
- Use tooltip rather than popover on settings page (spadgett@redhat.com)
- Show loading message until builders are loaded (spadgett@redhat.com)
- Fix error manually starting first build in Web Console (spadgett@redhat.com)
- Support rolling deployment hooks (ironcladlou@gmail.com)
- Remove Deployment resource (ironcladlou@gmail.com)
- Add --selector support to osadm registry (agoldste@redhat.com)
- Don't show get empty project message if project has monopods
  (spadgett@redhat.com)
- Improving/Adding/Refactoring logging messages (j.hadvig@gmail.com)
- Update labels and styles for create flow (spadgett@redhat.com)
- fix remove-user/group validation (deads@redhat.com)
- new-app: Add ability to specify a context directory
  (kargakis@users.noreply.github.com)
- Flip-flop priorities so that we distribute vips evenly. (smitram@gmail.com)
- Force refresh of projects when OpenShift Origin clicked (spadgett@redhat.com)
- pod/build delete sync (bparees@redhat.com)
- 'cat' here document rather than 'echo' (mjisyang@gmail.com)
- Fix ProjectNodeSelector config (jliggitt@redhat.com)
- Update vmware fedora version to be consistent (dmcphers@redhat.com)
- Disable `Next` button unless source URL is valid (spadgett@redhat.com)
- Added the deployment cancellation command to the CLI (abhgupta@redhat.com)
- Wait for service account before creating pods (jliggitt@redhat.com)
- system:node, system:sdn-reader, system:sdn-manager roles
  (jliggitt@redhat.com)
- Warn about pods with containers in bad states (spadgett@redhat.com)
- Update openshift-object-describer and k8s-label-selector dependencies
  (spadgett@redhat.com)
- Formatting fixes (dmcphers@redhat.com)
- UPSTREAM: resize: Enable resource type/name syntax
  (kargakis@users.noreply.github.com)
- Add minlength to name field on project create form (spadgett@redhat.com)
- Rename 'Management Console' to 'Web Console' (jliggitt@redhat.com)
- Updated image name in sample-app's pullimages.sh script (maszulik@redhat.com)
- UPSTREAM: kube: add pull secrets to service accounts (deads@redhat.com)
- Beef up osc label help message (kargakis@users.noreply.github.com)
- Bug 1223252: UPSTREAM: label: Invalidate empty or invalid value labels
  (kargakis@users.noreply.github.com)
- Fix repo name (dmcphers@redhat.com)
- Bug 1214205 - editor must always use the original object namespace when
  trying to update (contact@fabianofranz.com)
- Unpack and change versions of Template objects in origin-version-change
  (mfojtik@redhat.com)
- Show build pods events together with build events on osc describe build
  (maszulik@redhat.com)
- Fail build after 30 minutes of errors. (maszulik@redhat.com)
- use kubernetes plugin list instead of custom os list (mturansk@redhat.com)
- Add ServiceAccount type to list of exposed kube resources
  (jliggitt@redhat.com)
- Setting deployment/cancellation reason based on constants
  (abhgupta@redhat.com)
- Enable service account admission, token controller, auth, bootstrap policy
  (jliggitt@redhat.com)
- UPSTREAM: Add groups to service account JWT (jliggitt@redhat.com)
- UPSTREAM: gate token controller until caches are filled (jliggitt@redhat.com)
- add configchange trigger to frontend deployments (bparees@redhat.com)
- Added volume plugins to match upstream (mturansk@redhat.com)
- Added deleteTemplates method to remove templates from namespace
  (steve.kuznetsov@gmail.com)
- #1224083 - Update openshift-jvm to 1.0.17 (slewis@fusesource.com)
- UPSTREAM: bump timeout back to previous time
  (kargakis@users.noreply.github.com)
- UPSTREAM: Reduce reaper poll interval and wait while resizing
  (kargakis@users.noreply.github.com)
- Don't error out when exposing a label-less service as a route
  (kargakis@users.noreply.github.com)
- Added Kube PVC to OS whitelist (mturansk@redhat.com)
- Adding deployment cancellation controller (abhgupta@redhat.com)
- Disable triggers while reaping a deploymentConfig
  (kargakis@users.noreply.github.com)
- Display error when processing a template fails. (cewong@redhat.com)
- Don't repeat builder images in image catalog (spadgett@redhat.com)
- Add json tag for NetworkConfig (jdetiber@redhat.com)
- Move mock client calls under testclient (kargakis@users.noreply.github.com)
- Make golint happier (kargakis@users.noreply.github.com)
- Omit internal field when empty (rhcarvalho@gmail.com)
- Add test-cmd test to validate that we can create using a stored template
  (cewong@redhat.com)
- bump(github.com/openshift/openshift-
  sdn):7752990d5095d92905752aa5165a3d65ba8195e6 (sdodson@redhat.com)
- [RPMs] add openshift-sdn-ovs subpackage to carry ovs scripts and ovs dep
  (sdodson@redhat.com)
- Fix port ordering for a service (spadgett@redhat.com)
- Bug 1216930 - fix runtime error in rollback --dry-run
  (contact@fabianofranz.com)
- Validate project and image stream namespaces and names (jliggitt@redhat.com)
- Support custom CA for registry pruning (agoldste@redhat.com)
- Avoid warning icon flicker for deployment configs (spadgett@redhat.com)
- add TODO for watching delete events; catch error on StartMaster; do not try
  to create clusternetwork if it already exists (rchopra@redhat.com)
- Project status should include pod information (ccoleman@redhat.com)
- handle secret types (deads@redhat.com)
- Make link show up again and pass along token to openshift-jvm
  (slewis@fusesource.com)
- Added test cases to verify that ActiveDeadlineSeconds is set
  (abhgupta@redhat.com)
- Use client config's CA for registry pruning (agoldste@redhat.com)
- Duplicate default value in create node config was wrong (ccoleman@redhat.com)
- Replace secrets in BuildConfig with LocalObjectReference (mfojtik@redhat.com)
- Move deployment config to etcdgeneric storage patterns (decarr@redhat.com)
- grammar fix (somalley@redhat.com)
- respect --api-version flag for osc login (deads@redhat.com)
- Setting ActiveDeadlineSeconds on the deployment hook pod
  (abhgupta@redhat.com)
- UPSTREAM: kube: tolerate fatals without newlines (deads@redhat.com)
- Setting max/default ActiveDeadlineSeconds on the deployer pod
  (abhgupta@redhat.com)
- Add func for pruning an image from a stream (agoldste@redhat.com)
- Simplify output in login and project (ccoleman@redhat.com)
- Expose routes from services (kargakis@users.noreply.github.com)
- UPSTREAM: expose: Use resource builder (kargakis@users.noreply.github.com)
- Issue 2358 - better handling of server url parsing in osc login
  (contact@fabianofranz.com)
- UPSTREAM: Attach pull secrets to pods (mfojtik@redhat.com)
- Handle change in imageChange trigger status for v1beta3 (ccoleman@redhat.com)
- Test changes caused by version defaults (ccoleman@redhat.com)
- Add origin-version-change script (ccoleman@redhat.com)
- Make v1beta3 the default storage version (ccoleman@redhat.com)
- Initial commit of v1 api (ccoleman@redhat.com)
- remove unnecessary double escape replacement and add validation to ensure no
  one is relying on the removed behavior (pweil@redhat.com)
- fix looping on a closed channel - bz1222853, bz1223274 (rchopra@redhat.com)
- add prune images command (agoldste@redhat.com)
- Use correct deployer annotation (jliggitt@redhat.com)
- update forbidden messages (deads@redhat.com)
- relax restrictions on bundle secret (deads@redhat.com)
- Retry stream updates when pruning (agoldste@redhat.com)
- fix e2e public master (deads@redhat.com)
- Helpful hints for osc deploy make osc status worse (ccoleman@redhat.com)
- Remove summary pruner (agoldste@redhat.com)
- Fix template decode error when using new-app to create from a named template
  (cewong@redhat.com)
- Update pruning tests (agoldste@redhat.com)
- Replace _pods.less with _components.less (sgoodwin@redhat.com)
- Reenable CPU profiling default (ccoleman@redhat.com)
- manage-node tests can't rely on scheduling in hack/test-cmd.sh
  (ccoleman@redhat.com)
- wip (agoldste@redhat.com)
- Delegate manifest deletion to original Repository (agoldste@redhat.com)
- Image Pruning (agoldste@redhat.com)
- Image pruning (agoldste@redhat.com)
- Image pruning (agoldste@redhat.com)
- Image pruning (agoldste@redhat.com)
- Image Pruning (agoldste@redhat.com)
- Image pruning (agoldste@redhat.com)
- Image pruning (agoldste@redhat.com)
- Add image pruning support (agoldste@redhat.com)
- UPSTREAM(docker/distribution): manifest deletions (agoldste@redhat.com)
- UPSTREAM(docker/distribution): custom routes/auth (agoldste@redhat.com)
- UPSTREAM(docker/distribution): add BlobService (agoldste@redhat.com)
- Making the deployer pod name deterministic  - deployer pod name is now the
  same as the deployment name  - if an unrelated pod exists with the same name,
  the deployment is set to Failed (abhgupta@redhat.com)
- UPSTREAM(docker/distribution): add layer unlinking (agoldste@redhat.com)
- Add an example for a quota tracked project (decarr@redhat.com)
- Refactor overview page, combine route/service blocks (jliggitt@redhat.com)
- static markup and styles for overview (sgoodwin@redhat.com)
- Update install-assets.sh to use curl (jliggitt@redhat.com)
- Add Labels field into DockerConfig type (mfojtik@redhat.com)
- Fix generic webhook URL display (cewong@redhat.com)
- Code cleanup: Leveraging golang swap (abhgupta@redhat.com)
- Builds from BuildConfig missing BuildParameters.Resources (decarr@redhat.com)
- Code cleanup for openshift admin manage-node (rpenta@redhat.com)
- Update the help on admin commands (ccoleman@redhat.com)
- Display metadata about images in describe (ccoleman@redhat.com)
- Considering existing deployments for deployment configs  - If a
  running/pending/new deployment exists, the config is requeued  - If multiple
  running/previous/new deployments exists, older ones are cancelled
  (abhgupta@redhat.com)
- Use upstream RunKubelet method to run kubelet (cewong@redhat.com)
- Reduce fuzz iterations (ccoleman@redhat.com)
- Print more info on image tags and images (ccoleman@redhat.com)
- Minor change to the ipfailover Dockerfile for consistency
  (bleanhar@redhat.com)
- Add admin prune command (decarr@redhat.com)
- test-cmd: Check for removed rc (kargakis@users.noreply.github.com)
- test-cmd: Check for removed rc (kargakis@users.noreply.github.com)
- Build output round trip test can have ':' (ccoleman@redhat.com)
- Refactor etcd server start (ccoleman@redhat.com)
- Refactor to match upstream (ccoleman@redhat.com)
- UPSTREAM: print more useful error (ccoleman@redhat.com)
- UPSTREAM: implement a generic webhook storage (ccoleman@redhat.com)
- UPSTREAM: Suppress aggressive output of warning (ccoleman@redhat.com)
- UPSTREAM: Disable UIs for Kubernetes and etcd (ccoleman@redhat.com)
- bump(github.com/GoogleCloudPlatform/kubernetes):6b6b47a777b4802c9c1360ea0d583
  da6cfec7363 (ccoleman@redhat.com)
- bump(etcd):v2.0.11 (ccoleman@redhat.com)
- Retry image import conflicts (ccoleman@redhat.com)
- Issue 2293 - fixes options help message (contact@fabianofranz.com)
- Add text-overflow: ellipsis style to project select (spadgett@redhat.com)
- remove extraneous escapes (bparees@redhat.com)
- More login tests (contact@fabianofranz.com)
- Set default project in login so we can generate a ctx name properly
  (contact@fabianofranz.com)
- Bug 1218126 - login needs to make use of token if provided
  (contact@fabianofranz.com)
- gofmt and doc changes for Go 1.4 (ccoleman@redhat.com)
- Issue 2322 - fixes pod rendering in deployments screen
  (contact@fabianofranz.com)
- Add osc stop and osc label (kargakis@users.noreply.github.com)
- Docker registry installed should be logged (ccoleman@redhat.com)
- Stop using ephemeral ports for integration tests (jliggitt@redhat.com)
- Remember token ttl, stop retrieving user/token from localStorage after
  expiration (jliggitt@redhat.com)
- Added Kubernetes PVClaimBinder to OpenShift (mturansk@redhat.com)
- Prune deployment utilities (decarr@redhat.com)
- Fix go cross compiler package names in release image (mfojtik@redhat.com)
- Describe project should show quota and resource limits (decarr@redhat.com)
- Set NOFILE to 128k/64k for master/node, set CORE=infinity
  (sdodson@redhat.com)
- UPSTREAM: Disable 'Timestamps' in Docker logs to prevent double-timestamps
  (mfojtik@redhat.com)
- Don't show undefined in error messages when error details incomplete
  (spadgett@redhat.com)
- gofmt fix (kargakis@users.noreply.github.com)
- Unbreak default profiling behavior (ccoleman@redhat.com)
- Set TTL on oauth tokens (jliggitt@redhat.com)
- Fix gofmt error (jliggitt@redhat.com)
- Use client.TransportFor to set an etcd transport (ccoleman@redhat.com)
- Expose kubernetes components as symlink binaries (ccoleman@redhat.com)
- Embed Kube binaries (ccoleman@redhat.com)
- bump(): add packages for kubelet/cloudprovider (ccoleman@redhat.com)
- Use secure csrf/session cookies when serving on HTTPS (jliggitt@redhat.com)
- Use rand.Reader directly to generate tokens (jliggitt@redhat.com)
- Add custom token generation functions (jliggitt@redhat.com)
- bump(github.com/RangelReale/osin):a9958a122a90a3b069389d394284283c19d58913
  (jliggitt@redhat.com)
- Update k8s-label-selector to 0.0.4 (spadgett@redhat.com)
- Rename user visible errors to s2i or source-to-image (ccoleman@redhat.com)
- Rename STIStrategy to SourceStrategy in v1beta3 (ccoleman@redhat.com)
- update sti image builder sti release (bparees@redhat.com)
- bump (github.com/openshift/source-to-
  image):ac0b2512c9f933afa985b056a7f3cbce1942cacb (bparees@redhat.com)
- Add create project to web console (spadgett@redhat.com)
- Update openshift-object-describer dependency to 0.0.9 (spadgett@redhat.com)
- add non-resource urls to role describer (deads@redhat.com)
- Ignore things that cannot be known in admission control (decarr@redhat.com)
- Prune builds (decarr@redhat.com)
- nits to config output (deads@redhat.com)
- fix rolebinding describer (deads@redhat.com)
- Persist a master count config variable to enable multi-master
  (ccoleman@redhat.com)
- Add integration tests to validate build controller HA tolerance
  (cewong@redhat.com)
- Improve image change controller HA tolerance (cewong@redhat.com)
- osc login stanza names (deads@redhat.com)
- don't write project request template (deads@redhat.com)
- Copy sdn scripts into node subpackage (sdodson@redhat.com)
- Transition to Kube 1.0 DNS schema (ccoleman@redhat.com)
- Add connect link to pod list for pods that expose jolokia port
  (slewis@fusesource.com)
- resize: Defer any kind except dcs to kubectl
  (kargakis@users.noreply.github.com)
- Move creation of Docker registry before osc login (mfojtik@redhat.com)
- Fix curl command in sample-app README (mfojtik@redhat.com)
- Validate user and identity objects on update (jliggitt@redhat.com)
- Make csrf and session cookies httpOnly (jliggitt@redhat.com)
- Ensure real DNS subjectAltNames precede IP DNS subjectAltNames in generated
  certs (jliggitt@redhat.com)
- Deployment configs on the web console, with deployments grouped
  (contact@fabianofranz.com)
- Add selector option to router. (smitram@gmail.com)
- OpenShift admin command to manage node operations (rpenta@redhat.com)
- Fix new-app build config image reference (cewong@redhat.com)
- Bug 1221041 - fixes example in osc env (contact@fabianofranz.com)
- update sdn types to work nicely in v1beta3 and osc (deads@redhat.com)
- Moved Node.js instructions to be with its own repo (sspeiche@redhat.com)
- Added clustered etcd example (mfojtik@redhat.com)
- Add test, include groups from virtual users in users/~ (deads@redhat.com)
- Initial group support (jliggitt@redhat.com)
- fix vagrant-fedora21 networking issue; update openshift-sdn version
  (rchopra@redhat.com)
- Add PullSecretName to v1beta1 (mfojtik@redhat.com)
- Set default policy for pod exec, port-forward, and proxy (cewong@redhat.com)
- Fix deploymentConfig defaulting (ironcladlou@gmail.com)
- log nested error (bparees@redhat.com)
- Fix the origin release image (ccoleman@redhat.com)
- flag.Addr should not default URLs to DefaultPort (ccoleman@redhat.com)
- in new-app flow: Fix where to get the port for the service, skip service
  generation if no port is exposed; fix the namespace use to check for resource
  existence (jcantril@redhat.com)
- UPSTREAM: Continue on errors in kubectl (ccoleman@redhat.com)
- Wrap navbar controls naturally for small screens (spadgett@redhat.com)
- Namespace deployment annotations for v1beta3 (ironcladlou@gmail.com)
- Remove entire os coverage package (dmcphers@redhat.com)
- Add osc resize (kargakis@users.noreply.github.com)
- Beef-up new-app help message (kargakis@users.noreply.github.com)
- Bug 1218971: Persist existing imageStream name in buildCofig
  (kargakis@users.noreply.github.com)
- Add support for PULL_DOCKERCFG_PATH to docker build strategy
  (mfojtik@redhat.com)
- Update strategies to inject pull dockercfg into builder containers
  (mfojtik@redhat.com)
- Card origin_devexp_567 - Add PullSecretName to all build strategies
  (mfojtik@redhat.com)
- Fix gofmt errors. (smitram@gmail.com)
- Add NodeSelector support to enable placement of router and ipfailover
  components. (smitram@gmail.com)
- Add support to deployments history in osc describe and deploy
  (contact@fabianofranz.com)
- add default conversion handling for imagestream kind (bparees@redhat.com)
- Fix conversion of output.DockerImageReference on v1beta3 builds
  (cewong@redhat.com)
- Migrate build and build config to latest patterns in storage
  (decarr@redhat.com)
- Refactor to match upstream (ccoleman@redhat.com)
- UPSTREAM: print more useful error (ccoleman@redhat.com)
- UPSTREAM: implement a generic webhook storage (ccoleman@redhat.com)
- UPSTREAM: Suppress aggressive output of warning (ccoleman@redhat.com)
- UPSTREAM: Ensure no namespace on create/update root scope types
  (jliggitt@redhat.com)
- UPSTREAM: Disable UIs for Kubernetes and etcd (ccoleman@redhat.com)
- bump(github.com/GoogleCloudPlatform/kubernetes):25d32ee5132b41c122fe2929f3c6b
  e7c3eb74f1d (ccoleman@redhat.com)
- Be more aggressive about input and output on build From (ccoleman@redhat.com)
- update user/~ to return a user, even without an backing etcd entry
  (deads@redhat.com)
- Sort projects by display name (spadgett@redhat.com)
- Cleanup coverage profiles from output (dmcphers@redhat.com)
- SDN integration (rchopra@redhat.com)
- Bug 1218971: new-app: Create input imageStream
  (kargakis@users.noreply.github.com)
- Add descriptions to all API fields (ironcladlou@gmail.com)
- Make stanzas in test-cmd.sh independent (kargakis@users.noreply.github.com)
- Remove deployment followed by pull/1986 (nakayamakenjiro@gmail.com)
- Add bash-completion support (nakayamakenjiro@gmail.com)
- Remove cpu.pprof (ccoleman@redhat.com)
- bump (github.com/openshift/source-to-
  image):14c0ebafd9875ddba45ad53c220c3886458eaa44 (bparees@redhat.com)
- Ensure ImageStreamTag is exposed in v1beta3 (ccoleman@redhat.com)
- Ensure build output in v1beta3 is in ImageStreamTag (ccoleman@redhat.com)
- Add processedtemplates to policy (ccoleman@redhat.com)
- Switch integration tests to v1beta3 (ccoleman@redhat.com)
- Allow POST on empty namespace (ccoleman@redhat.com)
- Switch default API version to v1beta3 (ccoleman@redhat.com)
- UPSTREAM: allow POST on all namespaces in v1beta3 (ccoleman@redhat.com)
- UPSTREAM: disable minions/status in v1 Kube api (ccoleman@redhat.com)
- Combine coverage (dmcphers@redhat.com)
- Get rid of overly complex loop in favor of two commands with local variables
  (sdodson@redhat.com)
- merge default config with user config (akostadi@redhat.com)
- Added support for project node selector (rpenta@redhat.com)
- Accept ImageStreamTag as an image trigger kind (ironcladlou@gmail.com)
- Implement a Rolling deployment strategy (ironcladlou@gmail.com)
- Hide failed monopods in project overview (spadgett@redhat.com)
- Add config for number of cpus and memory (dmcphers@redhat.com)
- add cluster-reader role (deads@redhat.com)
- Show routes on project overview page (spadgett@redhat.com)
- Initialize object labels while processing a template
  (kargakis@users.noreply.github.com)
- Fix error loading view during karma tests (jliggitt@redhat.com)
- Allow process to output a template (ccoleman@redhat.com)
- Hide build pods based on annotations (spadgett@redhat.com)
- Updated tests for generic webhook (maszulik@redhat.com)
- Added support for gogs webhooks in github webhook, also removed requirement
  for User-Agent (maszulik@redhat.com)
- 'osadm create-api-client-config' was overwriting the client certificate with
  the CA (bleanhar@redhat.com)
- Morse code change - dah to dit (dots). (smitram@gmail.com)
- annotate build pods (bparees@redhat.com)
- Only show 'None' when labels is empty (spadgett@redhat.com)
- merge env statements when concatenating (bparees@redhat.com)
- Annotate generated hosts (jliggitt@redhat.com)
- build openshift-pod rpm (tdawson@redhat.com)
- Add `osc env` command for setting and reading env (ccoleman@redhat.com)
- Clean up various help commands (ccoleman@redhat.com)
- Handle 'Cancelled' and 'Error' build status in the web console
  (spadgett@redhat.com)
- Card origin_devexp_286 - Added ssh key-based access to private git
  repository. (maszulik@redhat.com)
- Fixed godoc for push secrets. (maszulik@redhat.com)
- fix grep and insert hostnames (rchopra@redhat.com)
- vagrant changes to support fedora21 (rchopra@redhat.com)
- Preventing multiple deployments from running concurrently
  (abhgupta@redhat.com)
- Empty state message for project overview (spadgett@redhat.com)
- update references to policy commands (deads@redhat.com)
- Issue 1509 - fix usage error in openshift start (contact@fabianofranz.com)
- osadm certs: inform user of file writes (lmeyer@redhat.com)
- osadm certs: provide command descriptions (lmeyer@redhat.com)
- osadm create-master-certs: no overwrite by default (lmeyer@redhat.com)
- reduce visibility of dockercfg not found error (bparees@redhat.com)
- Fix watching builds with fields filters (cewong@redhat.com)
- hack/common.sh uses the `which` command (akostadi@redhat.com)
- allow assigning floating IPs to openstack VMs (akostadi@redhat.com)
- VM prefixes for easy sharing AMZ and openstack accounts (akostadi@redhat.com)
- properly relativize paths (deads@redhat.com)
- Removed requirement for content-type in generic webhook, and added testcase
  for gitlab webhook push event. (maszulik@redhat.com)
- build-chain: s/repository/stream (kargakis@users.noreply.github.com)
- Add resource type descriptions to details sidebar (spadgett@redhat.com)
- Grammar fix in README (pmorie@gmail.com)
- UPSTREAM: Subresources inherit parent scope (ccoleman@redhat.com)
- Review comments (ccoleman@redhat.com)
- Detect and merge conflicts during osc edit (ccoleman@redhat.com)
- Exclude registered resources from latest.RESTMapper (ccoleman@redhat.com)
- UPSTREAM: print more useful error (ccoleman@redhat.com)
- UPSTREAM: legacy root scope should set NamespaceNone (ccoleman@redhat.com)
- UPSTREAM: SetNamespace should ignore root scopes (ccoleman@redhat.com)
- Perma-deflake TestDNS (ccoleman@redhat.com)
- Bug 1214229 - project admin cannot start build from another build
  (cewong@redhat.com)
- Add webhook to policy (ccoleman@redhat.com)
- Implement webhooks in v1beta3 (ccoleman@redhat.com)
- UPSTREAM: implement a generic webhook storage (ccoleman@redhat.com)
- change etcd paths (deads@redhat.com)
- Fix issues found by golint or govet within the build code (cewong@redhat.com)
- make project cache handle cluster policy (deads@redhat.com)
- cluster policy commands (deads@redhat.com)
- split cluster policy from local policy (deads@redhat.com)
- update for new STI request structure (bparees@redhat.com)
- bump (github.com/openshift/source-to-
  image):e71f7da750b1d81285597afacea8e365a991f04d (bparees@redhat.com)
- add all possible ips to the serving certs (deads@redhat.com)
- Remove deletion of registry pod from test-cmd (agoldste@redhat.com)
- Preserve scaling factor of prior deployment (ironcladlou@gmail.com)
- Change base paths for our resources (ccoleman@redhat.com)
- default node names always lowercase (deads@redhat.com)
- don't apply template if project exists (deads@redhat.com)
- Reenable deploy_trigger_test (agoldste@redhat.com)
- Use v1beta3 ObjectMeta for Route rather than internal representation
  (jimmidyson@gmail.com)
- Initial Image Metadata proposal (mfojtik@redhat.com)
- README.md: Use sudo in docker commands (stefw@redhat.com)
- Revert "Reenable deploy_trigger_test" (ccoleman@redhat.com)
- Implement a simple Git server for hosting repos (ccoleman@redhat.com)
- generic webhook should handle Git post-receive (ccoleman@redhat.com)
- bump(github.com/AaronO/go-git-http):0ebecedc64b67a3a8674c56724082660be48216e
  (ccoleman@redhat.com)
- properly handle bad projectRequestTemplates (deads@redhat.com)
- Add Browse -> Events page (spadgett@redhat.com)
- Wait for project to be deleted in hack/test-cmd.sh (ccoleman@redhat.com)
- Reenable deploy_trigger_test (agoldste@redhat.com)
- fix handling of imagestreamimage kinds in v1b1 (bparees@redhat.com)
- missed name when switching to new keys (pweil@redhat.com)
- Ignore openshift.local.* in test-go.sh (agoldste@redhat.com)
- Add conversion.go for generating conversions (ccoleman@redhat.com)
- Fix grep for registry pod in e2e (agoldste@redhat.com)
- Refactor to match upstream changes (ccoleman@redhat.com)
- UPSTREAM: kube: register types with gob (deads@redhat.com)
- UPSTREAM: Encode binary assets in ASCII only (jliggitt@redhat.com)
- UPSTREAM: Disable systemd activation for DNS (ccoleman@redhat.com)
- UPSTREAM: Handle missing resolv.conf (ccoleman@redhat.com)
- UPSTREAM: Suppress aggressive output of warning (ccoleman@redhat.com)
- UPSTREAM: add context to ManifestService methods (rpenta@redhat.com)
- UPSTREAM: Ensure no namespace on create/update root scope types
  (jliggitt@redhat.com)
- UPSTREAM: Disable UIs for Kubernetes and etcd (ccoleman@redhat.com)
- bump(github.com/GoogleCloudPlatform/kubernetes):c07896ee358addb44cc063eff3db1
  fcd0fe9767b (ccoleman@redhat.com)
- NodeController has been moved (ccoleman@redhat.com)
- Revert "Added support for project node selector" (ccoleman@redhat.com)
- Remove namespace conflict (kargakis@users.noreply.github.com)
- Use unified diff output for testing (nagy.martin@gmail.com)
- Link to the github page for github repositories (nagy.martin@gmail.com)
- Rename no syncing var (dmcphers@redhat.com)
- Added support for project node selector (rpenta@redhat.com)
- Fix not-a-function errors navigating between pages (spadgett@redhat.com)
- Separate 'Example' field in cli help (contact@fabianofranz.com)
- Make indentation consistent in help and usage (contact@fabianofranz.com)
- Adjust usage on several commands (contact@fabianofranz.com)
- Restores usage to cli templates (contact@fabianofranz.com)
- Use default port to proxy to backend (jliggitt@redhat.com)
- add php stream to repo list (bparees@redhat.com)
- Fix formatting and typos (dmcphers@redhat.com)
- describe: name/namespace to namespace/name syntax fix
  (kargakis@users.noreply.github.com)
- new-app: Use the right image stream for the build from
  (kargakis@users.noreply.github.com)
- Remove trailing spaces (rhcarvalho@gmail.com)
- Improve cleanup script (rhcarvalho@gmail.com)
- Fix formatting in sample-app/README.md (rhcarvalho@gmail.com)
- vagrant: fix creating minion config when provisioning master
  (thaller@redhat.com)
- Fix gofmt complaint (nakayamakenjiro@gmail.com)
- Fixing typos (dmcphers@redhat.com)
- Add cursor pointer to service component (sgoodwin@redhat.com)
- UPSTREAM Reject unbounded cpu and memory pods if quota is restricting it
  #7003 (decarr@redhat.com)
- osadm registry: require client cert when secure (agoldste@redhat.com)
- grant admin and edit access to secrets (deads@redhat.com)
- Allow registry to auto-provision image streams (agoldste@redhat.com)
- Bug 1214548 (somalley@redhat.com)
- make the new-project cli display the correct message on denial
  (deads@redhat.com)
- refactor bulk to take the interfaces it needs, not factory (deads@redhat.com)
- use a template for requested projects (deads@redhat.com)
- fix template processing to handle slices (deads@redhat.com)
- do not rewrite certs unless route has changed (pweil@redhat.com)
- refactor cert manager to allow testing, implement delete functionality
  (pweil@redhat.com)
- promote commands out of experimental (deads@redhat.com)
- Add pod logs and build logs to default policy constants (cewong@redhat.com)
- Fix minor deploy cmd typo (ironcladlou@gmail.com)
- object-describer 0.0.7, build bindata (jliggitt@redhat.com)
- Restyle of overview elements (sgoodwin@redhat.com)
- Object sidebar (jforrest@redhat.com)
- Add word-break mixin (sgoodwin@redhat.com)
- Highlight elements that are currently selected (jforrest@redhat.com)
- Style changes (sgoodwin@redhat.com)
- Object sidebar (jforrest@redhat.com)
- change policy binding names (deads@redhat.com)
- add cluster policy resources (deads@redhat.com)
- Generate webhook URLs from the client (ccoleman@redhat.com)
- Expose (broken) webhooks to v1beta3 (ccoleman@redhat.com)
- osc start-build should be able to trigger webhook (ccoleman@redhat.com)
- UPSTREAM: Allow URL to be generated by request.go (ccoleman@redhat.com)
- osc new-app shouldn't pull when image is chained (ccoleman@redhat.com)
- Improve ISTag image not found error response (agoldste@redhat.com)
- Invert the default behavior for osadm registry/router (ccoleman@redhat.com)
- add tracing in resolvimagestreamreference (bparees@redhat.com)
- properly handle external kube proxy case (deads@redhat.com)
- freshen template syntax (bparees@redhat.com)
- Use a safer delete of registry pod in test-cmd (agoldste@redhat.com)
- Deployment hooks inherit resources and working dir (ironcladlou@gmail.com)
- UPSTREAM: Handle conversion of boolean query parameters with a value of
  'false' (cewong@redhat.com)
- Allow 1 ImageStream tag to track another (agoldste@redhat.com)
- Fix build image change controller possible panic (agoldste@redhat.com)
- bump(docker/spdystream):e372247595b2edd26f6d022288e97eed793d70a2
  (agoldste@redhat.com)
- Make hook containers inherit environment (ironcladlou@gmail.com)
- Add long help to osc project (nakayamakenjiro@gmail.com)
- projectrequest get message (deads@redhat.com)
- explicitly set the project to avoid depending on project cache refresh
  (deads@redhat.com)
- if AllowDisabledDocker, allow docker to be missing (deads@redhat.com)
- gofmt fix (kargakis@users.noreply.github.com)
- new-app: Add image tag in generated imageStream
  (kargakis@users.noreply.github.com)
- Create build log subresource in the style of upstream pod log
  (cewong@redhat.com)
- UPSTREAM: Use Pod.Spec.Host instead of Pod.Status.HostIP for pod subresources
  (cewong@redhat.com)
- Dump metrics and run a CPU profile in hack/test-cmd (ccoleman@redhat.com)
- Set GOMAXPROCS by default (ccoleman@redhat.com)
- Return a template object from template process (ccoleman@redhat.com)
- only allow trusted env variables in sti builder container
  (bparees@redhat.com)
- Add v1beta3 cut of builds (ccoleman@redhat.com)
- Cleanup sysconfig values as everything is now in a config file
  (sdodson@redhat.com)
- add logout command (deads@redhat.com)
- Add replicated zookeeper example (mfojtik@redhat.com)
- Force no color in grep (ccoleman@redhat.com)
- Add a deploy command (ironcladlou@gmail.com)
- UPSTREAM: Switch kubelet log command to use pod log subresource
  (cewong@redhat.com)
- [RPMs] Move clients to common package and add dockerregistry subpkg
  (sdodson@redhat.com)
- force predictable ordering of removing users from a project
  (deads@redhat.com)
- refactor ict to remove from/image parameters (bparees@redhat.com)
- Replace docker-registry-*.json with osadm registry (agoldste@redhat.com)
- Use true generic objects in templates (ccoleman@redhat.com)
- Match changes to make []runtime.Object cleaner (ccoleman@redhat.com)
- UPSTREAM: Support unknown types more cleanly (ccoleman@redhat.com)
- UPSTREAM: add HasAny (deads@redhat.com)
- Hide images section when no images detected in template (cewong@redhat.com)
- Disable registry liveness probe to support v1 & v2 (agoldste@redhat.com)
- Web Console: Fix problems creating from templates (spadgett@redhat.com)
- WIP: displayName annotation (somalley@redhat.com)
- Fixed the sample-app readme (maszulik@redhat.com)
- Fix error handling of osc project (nakayamakenjiro@gmail.com)
- Update console for v2 image IDs (agoldste@redhat.com)
- Enable building v2 registry image (agoldste@redhat.com)
- Add info about Docker 1.6 to README (agoldste@redhat.com)
- [RPMs] Require docker >= 1.6.0 (sdodson@redhat.com)
- Require Docker 1.6 for node startup (agoldste@redhat.com)
- v2 registry updates (agoldste@redhat.com)
- UPSTREAM: add context to ManifestService methods (rpenta@redhat.com)
- bump(docker/distribution):62b70f951f30a711a8a81df1865d0afeeaaa0169
  (agoldste@redhat.com)
- Pass --force to docker push if needed (agoldste@redhat.com)
- * Add support for local-source configuration (jhonce@redhat.com)
- bad file references due to moved config (deads@redhat.com)
- Issue 1480 - switched to using goautoneg package for parsing accept headers
  (maszulik@redhat.com)
- UPSTREAM: Fix getting services in expose cmd
  (kargakis@users.noreply.github.com)
- Tests for new-app (kargakis@users.noreply.github.com)
- Rework new-app (kargakis@users.noreply.github.com)
- Remove experimental generate command (kargakis@users.noreply.github.com)
- UPSTREAM: cobra loses arguments with same value as subcommand
  (deads@redhat.com)
- bump(github.com/spf13/cobra):ebb2d55f56cfec37ad899ad410b823805cc38e3c
  (contact@fabianofranz.com)
- bump(github.com/spf13/pflag):60d4c375939ff7ba397a84117d5281256abb298f
  (contact@fabianofranz.com)
- make openshift start --write-config take a dir (deads@redhat.com)
- Add resource requirements to deployment strategy (decarr@redhat.com)
- don't let editors delete a project (deads@redhat.com)
- Show icons embedded as data uris in template and image catalogs in console
  (jforrest@redhat.com)
- Fix formatting (dmcphers@redhat.com)
- Handle portalIP 'None' and empty service.spec.ports (spadgett@redhat.com)
- Start/Rerun a build from the console (j.hadvig@gmail.com)
- Work around 64MB tmpfs limit (agoldste@redhat.com)
- UPSTREAM: describe: Support resource type/name syntax
  (kargakis@users.noreply.github.com)
- Add Deployment to v1beta3 (ccoleman@redhat.com)
- doc: fix instructions in example doc (mjisyang@gmail.com)
- Fix typo (rhcarvalho@gmail.com)
- Change available loglevel with openshift (nakayamakenjiro@gmail.com)
- default certificate support (pweil@redhat.com)
- Fixes as per @smarterclayton review comments. (smitram@gmail.com)
- Rename from ha*config to ipfailover. Fixes and cleanup as per @smarterclayton
  review comments. (smitram@gmail.com)
- Complete --delete functionality. (smitram@gmail.com)
- fix demo config (smitram@gmail.com)
- Convert to plugin code, add tests and use replica count in the keepalived
  config generator. (smitram@gmail.com)
- Checkpoint ha-config work. Add HostNetwork capabilities. Add volume mount to
  container. (smitram@gmail.com)
- Add HA configuration proposal. (smitram@gmail.com)
- Add new ha-config keepalived failover service container code, image and
  scripts. (smitram@gmail.com)
- Hide ugly output from osc status --help (nakayamakenjiro@gmail.com)
- Use unminified css on login page (jliggitt@redhat.com)
- sort projects (somalley@redhat.com)
- use CheckErr for pretty messages (deads@redhat.com)
- Add route to v1beta3 (ccoleman@redhat.com)
- add osadm to docker image (deads@redhat.com)
- Bug 1215014 - hostname for the node a pod is on is showing up as unknown due
  to an api change (jforrest@redhat.com)
- Embed the openshift-jvm console (jforrest@redhat.com)
- Added Node.js simple example workflow (sspeiche@redhat.com)
- migrate roles and bindings to new storage (deads@redhat.com)
- UPSTREAM: cobra loses arguments with same value as subcommand
  (deads@redhat.com)
- allow login with file that doesn't exist yet (deads@redhat.com)
- UPSTREAM Normalize to lower resource names in quota admission
  (decarr@redhat.com)
- [RPMs] Add socat and util-linux dependencies for node (sdodson@redhat.com)
- make request-project switch projects (deads@redhat.com)
- make project delegatable (deads@redhat.com)
- make osc login more userfriendly (deads@redhat.com)
- Produce events from deployment in failure scenarios (decarr@redhat.com)
- Deployments page throws JS error, still referencing /images when should be
  getting imageStreams (jforrest@redhat.com)
- Allow insecure registries for image import (ccoleman@redhat.com)
- Allow image specs of form foo:500/bar (ccoleman@redhat.com)
- Adopt multi-port services changes (spadgett@redhat.com)
- Validate ImageStreams in triggers (ironcladlou@gmail.com)
- enable stats listener for haproxy (pweil@redhat.com)
- UPSTREAM Fix nil pointer that can happen if no container resources are
  supplied (decarr@redhat.com)
- Initial work on multi-context html5 handling (jliggitt@redhat.com)
- Issue 1562 - relativize paths in client config file
  (contact@fabianofranz.com)
- Bug 1213648 - switch to a valid project after logging in
  (contact@fabianofranz.com)
- more tests (deads@redhat.com)
- make test-integration.sh allow single test (deads@redhat.com)
- add imagestream validation (deads@redhat.com)
- Disable building v2 registry image (agoldste@redhat.com)
- Fix URL for build webhooks docs in console + README (j.hadvig@gmail.com)
- Build controller logs events when failing to create pods (decarr@redhat.com)
- Forbidden resources should not break new-app (ccoleman@redhat.com)
- The order of "all" should be predictable (ccoleman@redhat.com)
- Add resource requirements to build parameters (decarr@redhat.com)
- try to match forbidden status to api version request (deads@redhat.com)
- Fix gofmt complaint (nakayamakenjiro@gmail.com)
- Add osadm to tarball (nakayamakenjiro@gmail.com)
- UPSTREAM Fixup event object reference generation to allow downstream objects
  (decarr@redhat.com)
- sample template messed up with v1beta3 (deads@redhat.com)
- Remove /tmp/openshift from README (ccoleman@redhat.com)
- correct registry and repository name (bparees@redhat.com)
- serve on multiple ports (pweil@redhat.com)
- UPSTREAM cherry pick make describeEvents DescribeEvents (decarr@redhat.com)
- add self-provisioned newproject (deads@redhat.com)
- Implement test config (ccoleman@redhat.com)
- migrate policy to new rest storage (deads@redhat.com)
- remove local .openshiftconfig (deads@redhat.com)
- Issue #1488 - added build duration and tweaked build counting in describer
  (maszulik@redhat.com)
- UPSTREAM: Allow resource builder to avoid fetching objects
  (jliggitt@redhat.com)
- Improve output of who-can command, fix oauthtokens bootstrap policy
  (jliggitt@redhat.com)
- Prepare v1beta3 Template types (ccoleman@redhat.com)
- Issue 1812 - subcommand 'options' must be exposed in every command that uses
  the main template (contact@fabianofranz.com)
- UPSTREAM Fix nil pointer in limit ranger (decarr@redhat.com)
- Add support to osc new-app from stored template (contact@fabianofranz.com)
- allow project admins to modify endpoints (deads@redhat.com)
- change openshiftconfig loading rules and files (deads@redhat.com)
- Replace all hardcoded default tags with DefaultImageTag
  (kargakis@users.noreply.github.com)
- Allow protocol prefixed docker pull specs (ccoleman@redhat.com)
- Support parameter substitution for all string fields (mfojtik@redhat.com)
- copy env variables into sti execution environment (bparees@redhat.com)
- Improve display of standalone build configs (ccoleman@redhat.com)
- Add build revision info to osc status (ccoleman@redhat.com)
- UPSTREAM: Suppress aggressive output of warning (ccoleman@redhat.com)
- Internal rename to v1beta3 (ccoleman@redhat.com)
- Update internal to v1beta3 for parity with Kube (ccoleman@redhat.com)
- Add round trip tests for images (ccoleman@redhat.com)
- Slightly simplify status output for service (ccoleman@redhat.com)
- Use extensions when editing a file (ccoleman@redhat.com)
- Fix issue in error reason detection (contact@fabianofranz.com)
- UPSTREAM: allow multiple changes in modifyconfig (deads@redhat.com)
- UPSTREAM: change kubeconfig loading order and update filename
  (deads@redhat.com)
- Bug 1201615 - Give swagger the correct base URL (ccoleman@redhat.com)
- Exposing the pod manifest file/dir option for the node in Origin
  (abhgupta@redhat.com)
- add db sample templates (bparees@redhat.com)
- UPSTREAM: resync api request resolver (deads@redhat.com)
- Add option to restrict google logins to custom domains (jliggitt@redhat.com)
- backends will be named based on the route ns/name, not the service name
  (pweil@redhat.com)
- UPSTREAM: Add URL parameters to proxy redirect Location header
  (cewong@redhat.com)
- missing json tag (deads@redhat.com)
- Remove trailing } (nagy.martin@gmail.com)
- Check /dev/tty if STDIN is not a tty (ccoleman@redhat.com)
- Add an edit command (ccoleman@redhat.com)
- stronger validation for tls termination type (pweil@redhat.com)
- Don't trigger a build if the namespaces differ (agoldste@redhat.com)
- UPSTREAM: It should be possible to have lists with mixed versions
  (ccoleman@redhat.com)
- Take storage version for kube/os as config params (ccoleman@redhat.com)
- First cut of resources without significant changes (ccoleman@redhat.com)
- Initial v1beta2 (experimental) cut (ccoleman@redhat.com)
- UPSTREAM: create parent dir structure when saving config to file
  (contact@fabianofranz.com)
- [BZ-1211516] Fix creating route even when choosing not to
  (jcantril@redhat.com)
- [BZ-1212362] Remove tls block for unsecure router generation from web console
  (jcantril@redhat.com)
- Some commenting here and there (kargakis@users.noreply.github.com)
- disallow empty static node names (deads@redhat.com)
- generate: Use Docker parser for validation
  (kargakis@users.noreply.github.com)
- change KUBECONFIG references to OPENSHIFTCONFIG (deads@redhat.com)
- restrict openshift loading chain to only openshift (deads@redhat.com)
- Use our mysql image (nagy.martin@gmail.com)
- Remove misleading comment from docs (rhcarvalho@gmail.com)
- Bump cadvisor, libcontainer (agoldste@redhat.com)
- Bug 1211235 - Validate user against OpenShift in case of docker login for v2
  registry (rpenta@redhat.com)
- UPSTREAM: allow multiple changes in modifyconfig (deads@redhat.com)
- bundle-secret updates (jliggitt@redhat.com)
- UPSTREAM: Fix a small regression on api server proxy after switch to v1beta3.
  #6701 (cewong@redhat.com)
- Convert OAuth registries to generic etcd (jliggitt@redhat.com)
- WIP: bundle-secret per feedback/rebase error (somalley@redhat.com)
- UPSTREAM: add flattening and minifying options to config view #6761
  (deads@redhat.com)
- Fix for Bug 1211210 in the ui where the tile list for builder images don't
  clear correctly in some situations. Remove animation transition css from
  _core, import new _component-animations and scope rule to .show-hide class
  (sgoodwin@redhat.com)
- bump(github.com/spf13/cobra): 9cb5e8502924a8ff1cce18a9348b61995d7b4fde
  (contact@fabianofranz.com)
- bump(github.com/spf13/pflag): 18d831e92d67eafd1b0db8af9ffddbd04f7ae1f4
  (contact@fabianofranz.com)
- [BUG 1211516] Fix service definition generation for v1beta3 when creating an
  app from source in the web console (jcantril@redhat.com)
- Show token expiration times (jliggitt@redhat.com)
- remove --username and --password from most osc commands (deads@redhat.com)
- Fix 'address already in use' errors in integration tests
  (jliggitt@redhat.com)
- Lengthen default access token lifetime to 1 day (jliggitt@redhat.com)
- Update keys for basicauth URL IDP to use OpenID standard claim names
  (jliggitt@redhat.com)
- Suppress swagger debug output (ccoleman@redhat.com)
- Bug 1209774: Trim windows newlines correctly (jliggitt@redhat.com)
- [RPMs] Generrate cross platform clients for MacOSX and Windows
  (sdodson@redhat.com)
- Add missing omitempty tags (ironcladlou@gmail.com)
- Minimize CPU churn in auth cache, re-enable integration test check
  (decarr@redhat.com)
- Remove all calls to the /images endpoint (jforrest@redhat.com)
- Correct kind, name, selfLink for ISTag, ISImage (agoldste@redhat.com)
- UPSTREAM: allow selective removal of kubeconfig override flags #6768
  (deads@redhat.com)
- Add e2e test coverage (ironcladlou@gmail.com)
- WIP (ironcladlou@gmail.com)
- Fix tests to be ifconfig 1.4.X compatible (epo@jemba.net)
- Implement deployment hooks (ironcladlou@gmail.com)
- Add limit range defaults to settings page (jforrest@redhat.com)
- build-chain: Fix test names for split (kargakis@users.noreply.github.com)
- Display login failures in osc (jliggitt@redhat.com)
- Add placeholder challenger when login is only possible via browser
  (jliggitt@redhat.com)
- Protect browsers from basic-auth CSRF attacks (jliggitt@redhat.com)
- Prevent duplicate resources in new-app (cewong@redhat.com)
- Disable refresh_token generation (jliggitt@redhat.com)
- Pass through remote OAuth errors (jliggitt@redhat.com)
- Create from template fails with JS error (jforrest@redhat.com)
- Enforce admission control of Origin resources in terminating namespaces
  (decarr@redhat.com)
- update osc config to use the same files as osc get (deads@redhat.com)
- UPSTREAM: make kubectl config behave more expectedly #6585 (deads@redhat.com)
- Add SyslogIdentifier=openshift-{master,node} respectively
  (sdodson@redhat.com)
- UPSTREAM: make APIInfoResolve work against subresources (deads@redhat.com)
- fix simulator urls (pweil@redhat.com)
- Provide easy delete of resources for new-app and generate
  (kargakis@users.noreply.github.com)
- Bug 1210659 - create from template fixes (jforrest@redhat.com)
- Cleanup the STI and Docker build output (mfojtik@redhat.com)
- UPSTREAM: Support setting up aliases for groups of resources
  (kargakis@users.noreply.github.com)
- Instructions to reload Network Manager (jliggitt@redhat.com)
- Update router integration test (ccoleman@redhat.com)
- TEMPORARY: osc build-logs failing in other namespace (ccoleman@redhat.com)
- Version lock e2e output tests (ccoleman@redhat.com)
- Master should send convertor, v1beta3 not experimental (ccoleman@redhat.com)
- Fix bug in error output (ccoleman@redhat.com)
- Refactor tests with port, command, testclient changes (ccoleman@redhat.com)
- Use Args instead of Command for OpenShift (ccoleman@redhat.com)
- Event recording has changed upstream, and changes to master/node args
  (ccoleman@redhat.com)
- Handle multi-port services in part (ccoleman@redhat.com)
- Update commands to handle change to cmd.Factory upstream
  (ccoleman@redhat.com)
- Refactor from upstream (ccoleman@redhat.com)
- UPSTREAM: Pass mapping version to printer always (ccoleman@redhat.com)
- UPSTREAM: entrypoint has wrong serialization flags in JSON
  (ccoleman@redhat.com)
- UPSTREAM: Ensure no namespace on create/update root scope types
  (jliggitt@redhat.com)
- UPSTREAM: add context to ManifestService methods (rpenta@redhat.com)
- UPSTREAM: Handle missing resolv.conf (ccoleman@redhat.com)
- UPSTREAM: Disable UI for Kubernetes (ccoleman@redhat.com)
- UPSTREAM: Disable systemd activation for DNS (ccoleman@redhat.com)
- UPSTREAM: Encode binary assets in ASCII only (jliggitt@redhat.com)
- UPSTREAM: support subresources in api info resolver (deads@redhat.com)
- UPSTREAM: Don't use command pipes for exec/port forward (agoldste@redhat.com)
- UPSTREAM: Prometheus can't be cross-compiled safely (ccoleman@redhat.com)
- bump(github.com/GoogleCloudPlatform/kubernetes):b12d75d0eeeadda1282f5738663bf
  e38717ebaf4 (ccoleman@redhat.com)
- [DEVEXP-457] Create application from source. Includes changes from jwforres,
  cewong, sgoodwin (jcantril@redhat.com)
- NetworkPlugin option in node config (rchopra@redhat.com)
- [RPMs]: tuned profiles get installed into /usr/lib not /usr/lib64
  (sdodson@redhat.com)
- separate tls and non-tls backend lookups (pweil@redhat.com)
- Now that we have better error handling, dont attempt login when we get a 0
  status code (jforrest@redhat.com)
- Update Browse->Images to be Image Streams in console (jforrest@redhat.com)
- Stop polling for pods in the console and open a websocket instead
  (jforrest@redhat.com)
- build-chain: Print only DOT output when specified
  (kargakis@users.noreply.github.com)
- Adding some more notes on probing containers (bleanhar@redhat.com)
- Auto provision image repo on push (agoldste@redhat.com)
- Setup aliases for imageStream* (kargakis@users.noreply.github.com)
- Remove admission/resourcedefaults (ccoleman@redhat.com)
- Update rebase-kube (ccoleman@redhat.com)
- Add OpenID identity provider (jliggitt@redhat.com)
- Refactor OAuth config (jliggitt@redhat.com)
- Widen the OpenShift CIDR to 172.30.0.0/16 (ccoleman@redhat.com)
- Add running builds and deployments to status output (ccoleman@redhat.com)
- Separate project status loggers (ccoleman@redhat.com)
- Add a generic injectable test client (ccoleman@redhat.com)
- UPSTREAM: Support a pluggable fake (ccoleman@redhat.com)
- Upgrade from etcd 0.4.6 -> 2.0.9 (ccoleman@redhat.com)
- bump(github.com/coreos/etcd):02697ca725e5c790cc1f9d0918ff22fad84cb4c5
  (ccoleman@redhat.com)
- Godeps.json formatting is wrong (ccoleman@redhat.com)
- probe delay (pweil@redhat.com)
- UPSTREAM: Don't use command pipes for exec/port forward (agoldste@redhat.com)
- stop swallowing errors (deads@redhat.com)
- allow everyone get,list access on the image group in openshift
  (deads@redhat.com)
- Fix loose links in README (kargakis@users.noreply.github.com)
- Adjust help template to latest version of Cobra (contact@fabianofranz.com)
- bump(github.com/inconshreveable/mousetrap):
  76626ae9c91c4f2a10f34cad8ce83ea42c93bb75C (contact@fabianofranz.com)
- bump(github.com/spf13/cobra): b78326bb16338c597567474a3ff35d76b75b804e
  (contact@fabianofranz.com)
- bump(github.com/spf13/pflag): 18d831e92d67eafd1b0db8af9ffddbd04f7ae1f4
  (contact@fabianofranz.com)
- UPSTREAM: make .Stream handle error status codes (deads@redhat.com)
- Test switching contexts with osc project (deads@redhat.com)
- set context namespace in generated .kubeconfig (deads@redhat.com)
- Add image streams to the types handled by web console. (cewong@redhat.com)
- perform initial commit to write config (pweil@redhat.com)
- OpenShift auth handler for v2 docker registry (rpenta@redhat.com)
- UPSTREAM: add context to ManifestService methods (rpenta@redhat.com)
- OAuth secret config (jliggitt@redhat.com)
- Customize messenger styling fix bug Bug 1203949 to correct sidebar display in
  ie and resized logo to fix ie issue (sgoodwin@redhat.com)
- Fix 'tito release' (sdodson@redhat.com)
- Project life-cycle updates (decarr@redhat.com)
- Fix nil ImageStreamGetter (agoldste@redhat.com)
- Image stream validations (agoldste@redhat.com)
- Enable namespace exists and namespace lifecycle admission controllers
  (decarr@redhat.com)
- More uniform use of %%{name} macro (sdodson@redhat.com)
- Add /etc/openshift to rpm packaging (sdodson@redhat.com)
- Updated #1525 leftovers in sample-app (maszulik@redhat.com)
- Bug 1206109: Handle specified tags that don't exist in the specified image
  repository (kargakis@users.noreply.github.com)
- Register lower and camelCase for v1beta1 (decarr@redhat.com)
- The build-logs command needs a cluster admin to run, make it clear in README
  (contact@fabianofranz.com)
- print builds as part of buildconfig description (bparees@redhat.com)
- only validate start args when NOT using config (deads@redhat.com)
- Validate CSRF in external oauth flow (jliggitt@redhat.com)
- Move labeling functions to util package (kargakis@users.noreply.github.com)
- Plumb CA and client cert options into basic auth IDP (jliggitt@redhat.com)
- add buildconfig reference field to builds (bparees@redhat.com)
- support subresources (deads@redhat.com)
- UPSTREAM: support subresources in api info resolver (deads@redhat.com)
- Move hostname detection warning to runtime (jliggitt@redhat.com)
- Make osc.exe work on Windows (jliggitt@redhat.com)
- add delays when handling retries so we don't tight loop (bparees@redhat.com)
- UPSTREAM: add a blocking accept method to RateLimiter
  https://github.com/GoogleCloudPlatform/kubernetes/pull/6314
  (bparees@redhat.com)
- Revert to handle error without glog.Fatal (nakayamakenjiro@gmail.com)
- display pretty strings for policy rule extensions (deads@redhat.com)
- remove dead parameters from openshift start (deads@redhat.com)
- UPSTREAM: Do not log errors where the event already exists
  (ccoleman@redhat.com)
- Implement an `osc status` command that groups resources by their
  relationships (ccoleman@redhat.com)
- Replace hostname -f with unmae -n (nakayamakenjiro@gmail.com)
- bump(github.com/gonum/graph):f6ac2b0f80f5a28ee70af78ce415393b37bcd6c1
  (ccoleman@redhat.com)
- Wrap proxy command (kargakis@users.noreply.github.com)
- go vet test (kargakis@users.noreply.github.com)
- Update config arg in Readme to be after command (ccoleman@redhat.com)
- Fix broken cli commands in README (ccoleman@redhat.com)
- Add description for --master option of openshift-master start
  (nakayamakenjiro@gmail.com)
- Use imageConfig in node (jliggitt@redhat.com)
- Output config errors better (jliggitt@redhat.com)
- Integrating help and usage templates in all commands
  (contact@fabianofranz.com)
- UPSTREAM Client must specify a resource version on finalize
  (decarr@redhat.com)
- Fix OAuth redirect (jliggitt@redhat.com)
- Show error on login redirect without token (jliggitt@redhat.com)
- Deprecate ImageRepository, add ImageStream (agoldste@redhat.com)
- UPSTREAM: Pass ctx to Validate, ValidateUpdate (agoldste@redhat.com)
- Issue 1529 - fix regression in help templates (contact@fabianofranz.com)
- fix typo (pweil@redhat.com)
- Remove the use of checkErr in our codebase (ccoleman@redhat.com)
- Add compile dependency on Kubernetes namespace controller (decarr@redhat.com)
- bump(github.com/GoogleCloudPlatform/kubernetes/pkg/namespace:8d94c43e705824f2
  3791b66ad5de4ea095d5bb32) (decarr@redhat.com)
- Adjust default log levels for web console and log errors when the local
  storage user store is unavailable (jforrest@redhat.com)
- Update sample app README to use login and project commands
  (contact@fabianofranz.com)
- Updated sample-app output to match current state of work
  (maszulik@redhat.com)
- Test PushSecretName via extended tests (mfojtik@redhat.com)
- Separate e2e-user config file in end to end (jliggitt@redhat.com)
- Uncommenting test for headless services (abhgupta@redhat.com)
- Replacing "None" for service PortalIP with constant (abhgupta@redhat.com)
- return updated build+buildconfig objects on update (bparees@redhat.com)
- Changing projects with empty namespace should succeed (ccoleman@redhat.com)
- add db images to sample repos (bparees@redhat.com)
- new-app should treat image repositories as more specific than docker images
  (ccoleman@redhat.com)
- UPSTREAM: Encode binary assets in ASCII only (jliggitt@redhat.com)
- Restore asset tests on Jenkins (jliggitt@redhat.com)
- Rewrite deployment ImageRepo handling (ironcladlou@gmail.com)
- Send a birthcry event when openshift node starts (pmorie@gmail.com)
- Temporarily remove asset build failures from Jenkins (jliggitt@redhat.com)
- Set unix LF EOL for shell scripts (itconsense@gmail.com)
- Updated STI binary (maszulik@redhat.com)
- Tweak OAuth config (jliggitt@redhat.com)
- Verify identity reference (jliggitt@redhat.com)
- Fix node yaml config serialization, unify config reading helper methods
  (jliggitt@redhat.com)
- Use struct literal to build a new pipeline
  (kargakis@users.noreply.github.com)
- bump(github.com/openshift/source-to-
  image):957c66bdbe15daca7b3af41f2c311af160473796 (maszulik@redhat.com)
- Remove osin example (kargakis@users.noreply.github.com)
- bump(golang.org/x/oauth2):c4932a9b59a60daa02a28db1bb7be39d6ec2e542
  (kargakis@users.noreply.github.com)
- Remove duplicate oauth2 library (kargakis@users.noreply.github.com)
- Update vagrant cluster commands (jliggitt@redhat.com)
- Add helper for p12 cert creation (jliggitt@redhat.com)
- Update vagrant cert wiring (jliggitt@redhat.com)
- Fix build logs with authenticated node (jliggitt@redhat.com)
- Serve node/etcd over https (jliggitt@redhat.com)
- Use the Fake cAdvisor interface on Macs (ccoleman@redhat.com)
- resolve from references when creating builds
  https://bugzilla.redhat.com/show_bug.cgi?id=1206052 (bparees@redhat.com)
- fix ResetBefore* methods (pweil@redhat.com)
- Add a forced version tagger for --use-version (sdodson@redhat.com)
- Teach our tito tagger to use vX.Y.Z tags (sdodson@redhat.com)
- Reset rpm specfile version to 0.0.1, add RPM build docs to HACKING.md
  (sdodson@redhat.com)
- UPSTREAM: Fixing accidental hardcoding of priority function weight
  (abhgupta@redhat.com)
- UPSTREAM: Removing EqualPriority from the list of default priorities
  (abhgupta@redhat.com)
- UPSTREAM: Remove pods from the assumed pod list when they are deleted
  (abhgupta@redhat.com)
- UPSTREAM: Updating priority function weight based on specified configuration
  (abhgupta@redhat.com)
- Fix switching between contexts that don't have a namespace explicit
  (contact@fabianofranz.com)
- osc login must check if cert data were provided through flags before saving
  (contact@fabianofranz.com)
- Make test-end-to-end use osc login|project (contact@fabianofranz.com)
- UPSTREAM: fix godep hash from bad restore (pweil@redhat.com)
- Add deprecation warnings for OAUTH envvars (jliggitt@redhat.com)
- expose oauth config in config (deads@redhat.com)
- print from repo info for sti builds (bparees@redhat.com)
- rebase refactoring (pweil@redhat.com)
- UPSTREAM: eliminate fallback to root command when another command is
  explicitly requested (deads@redhat.com)
- UPSTREAM: Tone down logging in Kubelet for cAdvisor being dead
  (ccoleman@redhat.com)
- UPSTREAM: Make setSelfLink not bail out (ccoleman@redhat.com)
- UPSTREAM: need to make sure --help flags is registered before calling pflag
  (contact@fabianofranz.com)
- UPSTREAM: Disable UIs for Kubernetes and etcd (ccoleman@redhat.com)
- UPSTREAM: Disable systemd activation for DNS (ccoleman@redhat.com)
- UPSTREAM: Handle missing resolv.conf (ccoleman@redhat.com)
- UPSTREAM: Remove cadvisor_mock.go (ccoleman@redhat.com)
- bump(github.com/GoogleCloudPlatform/kubernetes):f057a25b5d37a496c1ce25fbe1dc1
  b1971266240 (pweil@redhat.com)
- Bug 1206109 - build-chain: Set tags correctly
  (kargakis@users.noreply.github.com)
- new-app: Avoid extra declaration (kargakis@users.noreply.github.com)
- Moved LabelSelector and LabelFilter to their own bower component
  (jforrest@redhat.com)
- Wrap describe command (kargakis@users.noreply.github.com)
- Add extra tests for DNS and prepare for Headless services
  (ccoleman@redhat.com)
- DRYed test cases: clarified recursion check (somalley@redhat.com)
- Support headless services via DNS, fix base queries (ccoleman@redhat.com)
- add tag info to buildparameter output (bparees@redhat.com)
- Console now on /console (ccoleman@redhat.com)
- Move common template labels out of the objects description field
  (ccoleman@redhat.com)
- Make docker push quiet in builders (maszulik@redhat.com)
- Handle unexpected server errors more thoroughly in RequestToken
  (ccoleman@redhat.com)
- Issue 1200: use single quotes when printing usage for string flags
  (contact@fabianofranz.com)
- Comments (jliggitt@redhat.com)
- Lock down *min dependencies (jliggitt@redhat.com)
- Split identity and user objects (jliggitt@redhat.com)
- add how to disable security to the readme (deads@redhat.com)
- UPSTREAM: Fix namespace on delete (jliggitt@redhat.com)
- UPSTREAM: Ensure no namespace on create/update root scope types
  (jliggitt@redhat.com)
- relativize paths for master config (deads@redhat.com)
- clean up admin commands (deads@redhat.com)
- Fix panic when Source is not specified in CustomBuild (mfojtik@redhat.com)
- new-app: Fix typo (kargakis@users.noreply.github.com)
- Make 'osc project' use the provided io.Writer (d4rkn35t0@gmail.com)
- Remove hard-coded padding (jliggitt@redhat.com)
- Make service dependencies considerably more strict (sdodson@redhat.com)
- Show warning on terminating projects and disable Create button
  (jforrest@redhat.com)
- Test build-chain in hack/test-cmd (kargakis@users.noreply.github.com)
- Bug 1206419 - Handle empty namespace slice plus message fix
  (kargakis@users.noreply.github.com)
- Adding the the kubernetes and (future) openshift services to the list of
  Master server names (bleanhar@redhat.com)
- Fixed problems with deployment tests (maszulik@redhat.com)
- Move build generation logic to new endpoints (maszulik@redhat.com)
- Copying Build Labels into build Pod. (maszulik@redhat.com)
- Issue #333, #528 - add number to builds (maszulik@redhat.com)
- Issue #408 - Remove PodName from Build object (maszulik@redhat.com)
- add-user became add-role-to-user (ccoleman@redhat.com)
- Move to upstream list/watch (decarr@redhat.com)
- show buildconfig in describe output (bparees@redhat.com)
- Update all references to the console on port 8444 (jforrest@redhat.com)
- Implement scaffolding to purge project content on deletion
  (decarr@redhat.com)
- Asset changes needed to support a non / context root.  Global redirect to
  asset server or dump of api paths when / is requested. (jforrest@redhat.com)
- Initial changes to support console being served from same port as API or as
  its own server on a separate port (jliggitt@redhat.com)
- Drop From field validation check (kargakis@users.noreply.github.com)
- Make overwrite-policy require confirmation (ccoleman@redhat.com)
- Add an official 'openshift admin' command (ccoleman@redhat.com)
- UPSTREAM: eliminate fallback to root command when another command is
  explicitly requested (deads@redhat.com)
- Add unit tests for PushSecretName (mfojtik@redhat.com)
- Bug 1206109 - Default empty tag slice to 'latest'
  (kargakis@users.noreply.github.com)
- Fix typo (pmorie@gmail.com)
- Specifying the correct kubeconfig file for the minions in a cluster
  (abhgupta@redhat.com)
- fix missing serialization tag (deads@redhat.com)
- master and node config files should not contain backsteps (deads@redhat.com)
- Add a client cache and remove log.Fatal behavior from session ended
  (ccoleman@redhat.com)
- UPSTREAM: Tone down logging in Kubelet for cAdvisor being dead
  (ccoleman@redhat.com)
- hack/test-cmd.sh is flaky on macs (ccoleman@redhat.com)
- build-chain: Fix default namespace setup (kargakis@users.noreply.github.com)
- Removing --master flag from the openshift-node service (abhgupta@redhat.com)
- Inherit LOGLEVEL in Build pods from OpenShift (mfojtik@redhat.com)
- Require to have 'dockercfg' Secret data for PushSecretName
  (mfojtik@redhat.com)
- return a forbidden api status object (deads@redhat.com)
- tidy up MasterConfig getter location (deads@redhat.com)
- Expand validation and status spec (ironcladlou@gmail.com)
- Allow to specify PushSecretName in BuildConfig Output (mfojtik@redhat.com)
- Issue 1349 - osc project supports switching by context name
  (contact@fabianofranz.com)
- Expose project status from underlying namespace (decarr@redhat.com)
- Test pod describe in hack/test-cmd.sh (ccoleman@redhat.com)
- Improve the general message flow for login (ccoleman@redhat.com)
- add missing json def (pweil@redhat.com)
- reaper: Use NOHANG pattern instead of waiting for all children.
  (mrunalp@gmail.com)
- Exposing the scheduler config file option (abhgupta@redhat.com)
- eliminate bad defaults in create-kubeconfig (deads@redhat.com)
- Added image repository reference From field to STIBuildStrategy
  (yinotaurus@gmail.com)
- Revert "Added image repository reference From field to STIBuildStrategy"
  (ccoleman@redhat.com)
- create-node-config command (deads@redhat.com)
- Remove old geard docs (pmorie@gmail.com)
- Added image repository reference From field to STIBuildStrategy
  (yinotaurus@gmail.com)
- Bug 1196138 add newline char for: openshift ex router and registry, output
  (sspeiche@redhat.com)
- Introduce deployment hook proposal (ironcladlou@gmail.com)
- delegate to kube method for unknown resource kinds (deads@redhat.com)
- Output build dependencies of a specific image repository
  (kargakis@users.noreply.github.com)
- add rule to allow self-subject access reviews (deads@redhat.com)
- go vet pkg (kargakis@users.noreply.github.com)
- bump(github.com/awalterschulze/gographviz):20d1f693416d9be045340150094aa42035
  a41c9e (kargakis@users.noreply.github.com)
- Remove GOFLAGS arguments from Makefile (ccoleman@redhat.com)
- Force OPENSHIFT_PROFILE to be tested (ccoleman@redhat.com)
- Fix web profiling (ccoleman@redhat.com)
- ImageStreamImage/ImageRepositoryTag virtual rsrcs (agoldste@redhat.com)
- handle case where we have no build start time (bparees@redhat.com)
- add validation calls when we delegate cert commands (deads@redhat.com)
- pass master and public-master urls to create-all-certs (deads@redhat.com)
- make test-cmd more reliable on travis by pre-minting certs (deads@redhat.com)
- Use semantic deep equal for comparison (ccoleman@redhat.com)
- Refactor 12 (ccoleman@redhat.com)
- Fixed buildlogs (maszulik@redhat.com)
- Add info messages for end-to-end (ccoleman@redhat.com)
- Convert travis to make check-test (ccoleman@redhat.com)
- Refactor 11 (ccoleman@redhat.com)
- Kubelet health check fails when not sent to hostname (ccoleman@redhat.com)
- Ensure integration tests run when Docker is not available
  (ccoleman@redhat.com)
- Add check-test in between check and test (ccoleman@redhat.com)
- Remove debug logging from image controller (ccoleman@redhat.com)
- Refactor 10 (ccoleman@redhat.com)
- Refactor 9 (ccoleman@redhat.com)
- Refactor 8 (ccoleman@redhat.com)
- Refactor 7 (ccoleman@redhat.com)
- Refactor 6 (ccoleman@redhat.com)
- Refactor 5 (ccoleman@redhat.com)
- Refactor 4 (ccoleman@redhat.com)
- Refactor 3 (ccoleman@redhat.com)
- Refactor 2 (ccoleman@redhat.com)
- Refactor 1 (ccoleman@redhat.com)
- UPSTREAM: Remove global map from healthz (ccoleman@redhat.com)
- UPSTREAM: Lazily init systemd for code that includes cadvisor but doesn't use
  it (ccoleman@redhat.com)
- UPSTREAM: Make setSelfLink not bail out (ccoleman@redhat.com)
- UPSTREAM: need to make sure --help flags is registered before calling pflag
  (contact@fabianofranz.com)
- UPSTREAM: Disable UIs for Kubernetes and etcd (ccoleman@redhat.com)
- UPSTREAM: Disable systemd activation for DNS (ccoleman@redhat.com)
- UPSTREAM: Handle missing resolv.conf (ccoleman@redhat.com)
- UPSTREAM: Remove cadvisor_mock.go (ccoleman@redhat.com)
- bump(github.com/GoogleCloudPlatform/kubernetes):c5f73516b677434d9cce7d07e460b
  b712c85e00b (ccoleman@redhat.com)
- Fix how OPENSHIFT_INSECURE is parsed (agoldste@redhat.com)
- Unset KUBECONFIG prior to hack/test-cmd.sh (ccoleman@redhat.com)
- Add build duration to web console (jforrest@redhat.com)
- Group all build extended tests into one file (mfojtik@redhat.com)
- Unify 'testutil' as package name in tests (mfojtik@redhat.com)
- Add test-extended.sh into Makefile (mfojtik@redhat.com)
- Add v2 registry (agoldste@redhat.com)
- UPSTREAM: use docker's ParseRepositoryTag when pulling images
  (agoldste@redhat.com)
- bump(docker/docker):c1639a7e4e4667e25dd8c39eeccb30b8c8fc6357
  (agoldste@redhat.com)
- bump(docker/distribution):70560cceaf3ca9f99bfb2d6e84312e05c323df8b
  (agoldste@redhat.com)
- bump(Sirupsen/logrus):2cea0f0d141f56fae06df5b813ec4119d1c8ccbd
  (agoldste@redhat.com)
- Pre-push ruby image for extended tests (mfojtik@redhat.com)
- handle trailing slashes (deads@redhat.com)
- Rework ui presentation and markup for builds view. Inclusion of noscript
  messages. Fix flex mixin which had ie 10 issue (sgoodwin@redhat.com)
- describe canceled build duration (bparees@redhat.com)
- Copy ImageRepository annotations to image (agoldste@redhat.com)
- add create-client command (deads@redhat.com)
- add identities for router and registry (deads@redhat.com)
- make login test avoid default kubeconfig chain (deads@redhat.com)
- Fix typo in extended docker test (mfojtik@redhat.com)
- Add dockerImageRepository to sample custom builder image repo
  (cewong@redhat.com)
- Removed copies of util.DefaultClientConfig (contact@fabianofranz.com)
- Fix panic during timeout (ironcladlou@gmail.com)
- Rebasing upstream to allow any number of kubeconfig files
  (contact@fabianofranz.com)
- UPSTREAM: allow any number of kubeconfig files (contact@fabianofranz.com)
- Reworked integration tests and added extended tests (mfojtik@redhat.com)
- Add ./hack/test-extended.sh (mfojtik@redhat.com)
- bump(github.com/matttproud/golang_protobuf_extensions/ext):ba7d65ac66e9da93a7
  14ca18f6d1bc7a0c09100c (kargakis@users.noreply.github.com)
- auto-provision policy bindings for bootstrapping (deads@redhat.com)
- properly handle missing policy document (deads@redhat.com)
- Issue 1348 - add support to expose persistent flags in help
  (contact@fabianofranz.com)
- Query the sample app during e2e to make sure MySQL responds
  (nagy.martin@gmail.com)
- Make console logging be enabled/disabled with log levels and scoped loggers
  (jforrest@redhat.com)
- use bootstrap policy constants for namespace and role default
  (deads@redhat.com)
- Set master IP correctly when starting kubernetes (jliggitt@redhat.com)
- added test case for empty name argument (somalley@redhat.com)
- examples, docs: describe user creation thoroughly (ttomecek@redhat.com)
- separate out bootstrap policy (deads@redhat.com)
- Remove docker IP from certs (jliggitt@redhat.com)
- Issue 1356 - setup should either save cert file or data
  (contact@fabianofranz.com)
- add completion time field to builds (bparees@redhat.com)
- Fix create-server-cert --signer-signer-{cert,key,serial} stutter
  (sdodson@redhat.com)
- Use new openshift/mysql-55-centos7 image for sample-app
  (nagy.martin@gmail.com)
- Change BindAddrArg to ListenArg (jliggitt@redhat.com)
- Fix grammar in README (cewong@redhat.com)
- Restore ability to run in http (jliggitt@redhat.com)
- Group node certs under a single directory (jliggitt@redhat.com)
- Initial config validation (jliggitt@redhat.com)
- Bug 1202672 - handle osc project without argument and no namespace set
  (contact@fabianofranz.com)
- UPSTREAM: remove exec ARGS log message (agoldste@redhat.com)
- Call sdNotify as soon as we've started OpenShift API server or node
  (sdodson@redhat.com)
- Make file references in config relative to config files (jliggitt@redhat.com)
- Preserve tag when v1 pull by id is possible (agoldste@redhat.com)
- Change how tags and status events are recorded (ccoleman@redhat.com)
- Use the dockerImageReference tag when pushed (ccoleman@redhat.com)
- Add an initial importer for Image Repositories (ccoleman@redhat.com)
- Add osc exec and port-forward commands (agoldste@redhat.com)
- Issue1317 - Added error logging to webhook controller (maszulik@redhat.com)
- Bug 1202686 - fixes forbidden error detection (contact@fabianofranz.com)
- add serializeable start config (deads@redhat.com)
- Error handling for web console, adds notification service and limits
  websocket re-connection retries (jforrest@redhat.com)
- Remove unwanted ng-if check from template catalog (jforrest@redhat.com)
- Minor message improvement (contact@fabianofranz.com)
- Generation command tests (cewong@redhat.com)
- Project is not required for a successful login (contact@fabianofranz.com)
- Introducing client login and setup - 'osc login' (contact@fabianofranz.com)
- Introducing client projects switching - 'osc project'
  (contact@fabianofranz.com)
- UPSTREAM: loader allows multiple sets of loading rules
  (contact@fabianofranz.com)
- Temporary fix to bump timeout to 300s (sdodson@redhat.com)
- Speed up installation of etcd (mfojtik@redhat.com)
- Handle wildcard resolution of services (ccoleman@redhat.com)
- Remove commented imports (kargakis@users.noreply.github.com)
- Make tests for the Docker parser more robust
  (kargakis@users.noreply.github.com)
- Allow test of only master to start successfully (ccoleman@redhat.com)
- Remove excessive logging (ccoleman@redhat.com)
- Tease apart separate concerns in RetryController (ccoleman@redhat.com)
- UPSTREAM: Don't hang when registering zero nodes (ccoleman@redhat.com)
- UPSTREAM: Temporarily relax annotations further (ccoleman@redhat.com)
- Always use port 8053 in integration tests (ccoleman@redhat.com)
- Add DockerImageReference type (agoldste@redhat.com)
- cancel-build: Use BuildLogs client method (kargakis@users.noreply.github.com)
- Removed extra tools imports (soltysh@gmail.com)
- Consolidate image reference generation/lookup (agoldste@redhat.com)
- path based ACLs (pweil@redhat.com)
- Add additional items to vm-provision-full (ccoleman@redhat.com)
- Switch default route dns suffix to "router.default.local" (smitram@gmail.com)
- Fixes to route allocator plugin PR as per @smarterclayton comments.
  (smitram@gmail.com)
- Add simple shard allocator plugin to autogenerate host names for routes based
  on service and namespace and hook it into the route processing [GOFM].
  (smitram@gmail.com)
- Various image updates (agoldste@redhat.com)
- fix start-build follow to stop following eventually (deads@redhat.com)
- Need more detail for contributing to v3 web console, started an architecture
  section (jforrest@redhat.com)
- Add more visual separation between builds, add copy to clipboard for webhook
  URLs (jforrest@redhat.com)
- integration test (deads@redhat.com)
- comments 2 (deads@redhat.com)
- check if template exists (bparees@redhat.com)
- Fix temporary platform builder image names for generation tools
  (cewong@redhat.com)
- Provide both a host and guest profile (sdodson@redhat.com)
- comments 1 (deads@redhat.com)
- allow bootstrap policy to span namespaces (deads@redhat.com)
- Fix bindata for rework page structure to use flexbox so that sidebar columns
  extend (jforrest@redhat.com)
- Bug 1200346 - need to convert quota values including SI prefixes for
  comparisions (jforrest@redhat.com)
- role and rolebinding printers and describers (deads@redhat.com)
- add role and rolebinding gets and lists (deads@redhat.com)
- Bug 1200684: Retrieve logs from failed builds
  (kargakis@users.noreply.github.com)
- add detail to forbidden message (deads@redhat.com)
- Rework page structure to use flexbox so that sidebar columns extend without
  dynamically setting height Adjustments to project-nav, primarily the label-
  selector so that it doesn't wrap and tighten up the look.
  (sgoodwin@redhat.com)
- Adds reaping capability to openshift. (mrunalp@gmail.com)
- Allow OpenShift to start on an airplane (ccoleman@redhat.com)
- UPSTREAM: Handle missing resolv.conf (ccoleman@redhat.com)
- Remove self closing tags (jliggitt@redhat.com)
- added notes for Vagrant users in sample-app README doc (somalley@redhat.com)
- Allow stored templates to be referenced from osc process (mfojtik@redhat.com)
- DNS default check should not be in server.Config (ccoleman@redhat.com)
- Move glog.Fatal to error propagation (jliggitt@redhat.com)
- Add cert validation options to requestheader (jliggitt@redhat.com)
- Make sure we don't swallow errors from inner Convert calls
  (maszulik@redhat.com)
- Bug 119409 - fix source URI generated by new-app (cewong@redhat.com)
- Management Console - Create from template (cewong@redhat.com)
- remove test-integration.sh from make test.  Resolves #1255 (pweil@redhat.com)
- Fixed URLs for webhooks presented in osc describe (maszulik@redhat.com)
- Add DNS support to OpenShift (ccoleman@redhat.com)
- UPSTREAM: Disable systemd activation for DNS (ccoleman@redhat.com)
- bump(github.com/skynetservices/skydns):f18bd625a71b5d013b6e6288d1c7ec8796a801
  88 (ccoleman@redhat.com)
- Make it easy to export certs to curl (ccoleman@redhat.com)
- Address some cli usage msg inconsistencies
  (kargakis@users.noreply.github.com)
- Remove use of Docker registry code (ccoleman@redhat.com)
- Remove dockerutils (ccoleman@redhat.com)
- UPSTREAM: docker/utils does not need to access autogen (ccoleman@redhat.com)
- Remove fake docker autogen package (ccoleman@redhat.com)
- create the buildconfig before creating the first imagerepo
  (bparees@redhat.com)
- Only build images during build-cross (ironcladlou@gmail.com)
- add redirect to list of approved verbs (deads@redhat.com)
- only resolve roles for bindings that matter (deads@redhat.com)
- Implement logs streaming option when starting a build
  (kargakis@users.noreply.github.com)
- Turn on quota related admission control plug-ins (decarr@redhat.com)
- use master ip address so that minions can reach master in multi-node setup.
  (pweil@redhat.com)
- allow current-user subjectaccessreview (deads@redhat.com)
- Use Docker parser when manipulating Dockerfiles
  (kargakis@users.noreply.github.com)
- Fix broken --parameters switch for process (mfojtik@redhat.com)
- Add test to exercise invalid parameter in Template (mfojtik@redhat.com)
- Return error when Template generator failed to generate parameter value
  (mfojtik@redhat.com)
- Fix escaping and value (dmcphers@redhat.com)
- Make sure image, namespace, and tag match (jliggitt@redhat.com)
- retry build errors (bparees@redhat.com)
- Fix new-app generation from local source (cewong@redhat.com)
- add namespace to internal route keys (pweil@redhat.com)
- Add templates to list of authorized resources (cewong@redhat.com)
- add export KUBECONFIG to osc create example
  (jeff.mccormick@crunchydatasolutions.com)
- switch access review users and groups to stringsets (deads@redhat.com)
- add subject access review integration tests (deads@redhat.com)
- Add BuildLogs method on Client (kargakis@users.noreply.github.com)
- Switch services to notify (sdodson@redhat.com)
- Add systemd notification on service startup completion (sdodson@redhat.com)
- bump(github.com/coreos/go-systemd): 2d21675230a81a503f4363f4aa3490af06d52bb8
  (sdodson@redhat.com)
- Revert "add annotations to image repos" (bparees@redhat.com)
- Bump sti-image-builder to STI v0.2 (sdodson@redhat.com)
- prevent changes to rolebinding.RoleRef (deads@redhat.com)
- Removed hack/config-go.sh from HACKING.md, it's not used anymore.
  (maszulik@redhat.com)
- Bug 1191960 - Remove --master from usage text for ex generate
  (cewong@redhat.com)
- Update Jenkins example with auth identity (jliggitt@redhat.com)
- fix nodelist defaulting (deads@redhat.com)
- Remove extra error check (kargakis@users.noreply.github.com)
- add annotations to image repos (bparees@redhat.com)
- fix osc create example to include cert dir kubconfig parameter
  (jeff.mccormick@crunchydatasolutions.com)
- add routes to services (pweil@redhat.com)
- exit with error if no tests are found (bparees@redhat.com)
- Add default template label to sample app templates (cewong@redhat.com)
- Fix router integration test (jliggitt@redhat.com)
- Add version command for all binaries/symlinks
  (kargakis@users.noreply.github.com)
- Updating ruby-20 links and image name so they point to new repo and image
  (j.hadvig@gmail.com)
- Better output for integration tests (ccoleman@redhat.com)
- Add RootResourceAccessReview to replace use of empty namespace
  (ccoleman@redhat.com)
- Better output for integration tests (ccoleman@redhat.com)
- UPSTREAM: Validate TCPSocket handler correctly (ccoleman@redhat.com)
- UPSTREAM: Relax constraints on container status while fetching container logs
  (vishnuk@google.com)
- Remove references to old volume source, handle endpoints change
  (ccoleman@redhat.com)
- UPSTREAM: Make setSelfLink not bail out (ccoleman@redhat.com)
- UPSTREAM: special command "help" must be aware of context
  (contact@fabianofranz.com)
- UPSTREAM: need to make sure --help flags is registered before calling pflag
  (contact@fabianofranz.com)
- UPSTREAM: Disable auto-pull when tag is "latest" (ccoleman@redhat.com)
- UPSTREAM: Disable UIs for Kubernetes and etcd (ccoleman@redhat.com)
- UPSTREAM: Add 'release' field to raven-go (ccoleman@redhat.com)
- bump(github.com/GoogleCloudPlatform/kubernetes):6241a211c8f35a6147aa3a0236f68
  0ffa8e11037 (ccoleman@redhat.com)
- bump(github.com/docker/docker):7d2188f9955d3f2002ff8c2e566ef84121de5217
  (kargakis@users.noreply.github.com)
- Wrap some commands to display OpenShift-specific usage msg
  (kargakis@users.noreply.github.com)
- support multiple go versions (bparees@redhat.com)
- fix up the jenkins example (bparees@redhat.com)
- extend the wait time for the project authorization cache (deads@redhat.com)
- Refactor deploy controllers to use RetryController (ironcladlou@gmail.com)
- Specify UI bind address in integration tests (jliggitt@redhat.com)
- reconnect --image (deads@redhat.com)
- Add htpasswd file param (jliggitt@redhat.com)
- Prevent challenging client from looping (jliggitt@redhat.com)
- Simplify auto-grant (jliggitt@redhat.com)
- use rpm instead of build haproxy from source (tdawson@redhat.com)
- fix nodelist access for kube master (deads@redhat.com)
- enforce authorization (deads@redhat.com)
- Put BuildConfig labels into metadata for sample-app (mfojtik@redhat.com)
- Revert "Support multiple Dockerfiles with custom-docker-builder"
  (bparees@redhat.com)
- Match project name validation to namespace name validation
  (jliggitt@redhat.com)
- Make "new-project --admin" reuse "add-user" (jliggitt@redhat.com)
- Add test to make sure osc can list new projects (jliggitt@redhat.com)
- Explicitly set --kubeconfig when starting node (sdodson@redhat.com)
- let project admins use resource access review (deads@redhat.com)
- Fix Used vs Max quota comparison in web console (jforrest@redhat.com)
- add context namespacing filter (deads@redhat.com)
- Re-enable project auth cache, add UI integration test (jliggitt@redhat.com)
- Output more details on pod details page in web console (jforrest@redhat.com)
- Allow multiple tags to refer to the same image (agoldste@redhat.com)
- Add controller retry support scaffolding (ironcladlou@gmail.com)
- UPSTREAM: Support AddIfNotPresent function (ironcladlou@gmail.com)
- Fix TLS EOF errors in log at start (jliggitt@redhat.com)
- Ensure create of master policy namespace happens after policy will allow it
  (jliggitt@redhat.com)
- Rework --kubeconfig handler, misc tweaks (jliggitt@redhat.com)
- make start.config immutable (deads@redhat.com)
- Fixed contextDir conversion after moving it from DockerBuildStrategy to
  BuildSource (maszulik@redhat.com)
- Make builder image naming consistent between build strategy describe
  (maszulik@redhat.com)
- Add verify-jsonformat to Travis (mfojtik@redhat.com)
- Fix formatting and errors in JSON files (mfojtik@redhat.com)
- Added ./hack/verify-jsonformat.sh (mfojtik@redhat.com)
- Support multiple Dockerfiles with custom-docker-builder
  (cole.mickens@gmail.com)
- Set global timer to autoupdate relative timestamps in the UI
  (jforrest@redhat.com)
- remove use_local env (bparees@redhat.com)
- Builds page - group builds by build config and show more details for build
  configs (jforrest@redhat.com)
- make build output optional (bparees@redhat.com)
- use ruby-20-centos7 in generated buildconfig (bparees@redhat.com)
- Use --from-build flag only for re-running builds
  (kargakis@users.noreply.github.com)
- Changed image names for ImageRepository objects, since it was using two
  exactly the same in different tests (maszulik@redhat.com)
- add liveness probe to router (pweil@redhat.com)
- Fix docs (kargakis@users.noreply.github.com)
- Rename 'Clean' to 'Incremental' in STI builder (mfojtik@redhat.com)
- Changed Info->Infof to have the variable printed (maszulik@redhat.com)
- Add optional e2e UI tests (jforrest@redhat.com)
- bump(github.com/openshift/source-to-
  image):c0c154efcba27ea5693c428bfe28560c220b4850 (mfojtik@redhat.com)
- Make cli examples consistent across OpenShift
  (kargakis@users.noreply.github.com)
- Validate usernames don't contain problematic URL sequences
  (jliggitt@redhat.com)
- Use a versioned printer for rollback configs (ironcladlou@gmail.com)
- Fix broken deployer pod GenerateName reference (ironcladlou@gmail.com)
- update must gather for policy (deads@redhat.com)
- Generate: handle image with multiple ports in EXPOSE statement
  (cewong@redhat.com)
- Update command parameter and help text to refer to single port
  (cewong@redhat.com)
- update readme to take advantage of authorization (deads@redhat.com)
- Make Clients API consistent (kargakis@users.noreply.github.com)
- Add htpasswd SHA/MD5 support (jliggitt@redhat.com)
- route definition requires name in metadata (akram.benaissi@free.fr)
- Rename BaseImage -> Image for DockerBuildStrategy to be consistent with
  STIBuilderStrategy about field naming (maszulik@redhat.com)
- Generate master and public-master .kubeconfig contexts (jliggitt@redhat.com)
- Add options to clear authorization headers for basic/bearer auth
  (jliggitt@redhat.com)
- better build names (bparees@redhat.com)
- pretty up policy describer (deads@redhat.com)
- UPSTREAM: get the keys from a string map (deads@redhat.com)
- create policy cache (deads@redhat.com)
- Add 'deny' password authenticator (jliggitt@redhat.com)
- Fix case (dmcphers@redhat.com)
- Add a command to install / check a registry (ccoleman@redhat.com)
- refactor authorization for sanity (deads@redhat.com)
- Card devexp_426 - Force clean builds by default for STI (maszulik@redhat.com)
- Better management of the systemd services (marek.goldmann@gmail.com)
- Fix loop period to stop pegging CPU, add project-spawner (decarr@redhat.com)
- List projects enforces authorization (decarr@redhat.com)
- fix formatting (bparees@redhat.com)
- Bug 1194487 - Fix generate command repository detection (cewong@redhat.com)
- Integration tests need to run in separate processes (ccoleman@redhat.com)
- Bug 1190578 - Should prompt clear error when generate an application list
  code in a non-source code repository. (cewong@redhat.com)
- copy build labels from buildconfig (bparees@redhat.com)
- Update test cases and docs to use `openshift ex router` (ccoleman@redhat.com)
- prevent privilege escalation (deads@redhat.com)
- Add a router command to install / check the routers (ccoleman@redhat.com)
- UPSTREAM: Expose converting client.Config files to Data (ccoleman@redhat.com)
- Remove cors headers from proxied connections (jliggitt@redhat.com)
- Strip auth headers before proxying, add auth headers on upgrade requests
  (jliggitt@redhat.com)
- Strip access_token param from requests in auth layer (jliggitt@redhat.com)
- Bug 1190576: Improve error message when trying to use non-existent reference
  (cewong@redhat.com)
- bump(github.com/openshift/source-to-
  image):ad5adc054311686baf316cd8bf91c4d42ae1bd4e (bparees@redhat.com)
- Improve help for creating / being added to new projects (jliggitt@redhat.com)
- Fix dangling commas in example json files (cewong@redhat.com)
- Add labels to templates (cewong@redhat.com)
- Vagrantfile: default libvirt box now with actual openshift
  (lmeyer@redhat.com)
- document sti images (bparees@redhat.com)
- Update docs (jliggitt@redhat.com)
- add namespaces to authorization rules (deads@redhat.com)
- Inline bootstrapped certs in client .kubeconfig files (jliggitt@redhat.com)
- UPSTREAM: Let .kubeconfig populate ca/cert/key data and basic-auth
  username/password in client configs (jliggitt@redhat.com)
- authorize non-resource urls (deads@redhat.com)
- use multiline in regex matching (bparees@redhat.com)
- Handle empty label selectors in web console (jforrest@redhat.com)
- Remove dead links from cli doc (kargakis@users.noreply.github.com)
- Capture errors from BuildParameters conversion (mfojtik@redhat.com)
- Fix integration (mfojtik@redhat.com)
- Move ContextDir under BuildSource (mfojtik@redhat.com)
- Add support for ContextDir in STI build (mfojtik@redhat.com)
- Fix Origin code to incorporate changes in STI (mfojtik@redhat.com)
- bump(github.com/openshift/source-to-image):
  1338bff33b5c46acc02840f88a9b576a1b1fa404 (mfojtik@redhat.com)
- bump(github.com/fsouza/go-
  dockerclient):e1e2cc5b83662b894c6871db875c37eb3725a045 (mfojtik@redhat.com)
- UPSTREAM: Surface load errors when reading .kubeconfig files
  (jliggitt@redhat.com)
- Handle k8s edge cases in the web console overview (jforrest@redhat.com)
- Give our local built docker images unique ids, and push that id
  (ccoleman@redhat.com)
- UPSTREAM: move setSelfLink logging to v(5) (deads@redhat.com)
- make useLocalImages the default and remove configurability
  (bparees@redhat.com)
- Fix build-in-docker.sh, use $(), not ${} (nagy.martin@gmail.com)
- validate route name and host (pweil@redhat.com)
- make sure rolebinding names are unique (deads@redhat.com)
- Use git fetch && reset if the given repo was cloned already
  (ppalaga@redhat.com)
- Replacing old openshift/nodejs-0-10-centos with new
  openshift/nodejs-010-centos7 (j.hadvig@gmail.com)
- Replace hardcoded-library-path (nakayamakenjiro@gmail.com)
- Fixing typos (dmcphers@redhat.com)
- Project is Kubernetes Namespace (decarr@redhat.com)
- Refactor deploy package for error handling support (ironcladlou@gmail.com)
- ignore selflinking error (deads@redhat.com)
- Implement a Template REST endpoint using the generic store
  (ccoleman@redhat.com)
- sync policy doc to reality (deads@redhat.com)
- Turn on resource quota manager to collect usage stats (decarr@redhat.com)
- Improve release tar naming (ironcladlou@gmail.com)
- Explicit build (ccoleman@redhat.com)
- Platform independent image builds (ironcladlou@gmail.com)
- bump(github.com/GoogleCloudPlatform/kubernetes/plugin/pkg/admission:c977a4586
  42b4dbd8c3ad9cfc9eecafc85fb6183) (decarr@redhat.com)
- Add compile dependency for Kubernetes admission control plugins
  (decarr@redhat.com)
- switch to kubernetes authorization info (deads@redhat.com)
- UPSTREAM: expose info resolver (deads@redhat.com)
- Remove GOPATH from build-in-docker.sh script (mfojtik@redhat.com)
- Unify all client Factories into one location (ccoleman@redhat.com)
- Move coverage output processing to the end (dmcphers@redhat.com)
- Switch to using request context mapper (jliggitt@redhat.com)
- router websocket support (pweil@redhat.com)
- add new-project command (deads@redhat.com)
- Add fixtures to test edge cases in the web console (jforrest@redhat.com)
- Fix htmlmin linebreak issue (jliggitt@redhat.com)
- Provide useful message when CERT_DIR is not set in install-registry.sh
  (mfojtik@redhat.com)
- Switch namespaced URL paths from ns/ to namespaces/ (jforrest@redhat.com)
- UPSTREAM: Distinguish between NamespaceAll and NamespaceDefault
  (ccoleman@redhat.com)
- use origin-base for base image (bparees@redhat.com)
- e2e without root fails because certs can't be viewed by wait_for_url
  (ccoleman@redhat.com)
- Tolerate Docker not being present when using all-in-one (ccoleman@redhat.com)
- Update registries to remove async channel (ccoleman@redhat.com)
- Compile time changes (ccoleman@redhat.com)
- UPSTREAM: Fix cross-namespace queries (ccoleman@redhat.com)
- UPSTREAM: Allow kubelet to run without Docker (ccoleman@redhat.com)
- UPSTREAM: Allow SetList to work against api.List (ccoleman@redhat.com)
- UPSTREAM: Disable auto-pull when tag is "latest" (ccoleman@redhat.com)
- UPSTREAM: Disable UIs for Kubernetes and etcd (ccoleman@redhat.com)
- UPSTREAM: Add 'release' field to raven-go (ccoleman@redhat.com)
- UPSTREAM: special command "help" must be aware of context
  (contact@fabianofranz.com)
- UPSTREAM: need to make sure --help flags is registered before calling pflag
  (contact@fabianofranz.com)
- bump(github.com/GoogleCloudPlatform/kubernetes):c977a458642b4dbd8c3ad9cfc9eec
  afc85fb6183 (ccoleman@redhat.com)
- Stop referencing kubecfg now that it is deleted upstream
  (ccoleman@redhat.com)
- Fix several typos (rhcarvalho@gmail.com)
- Note on using docker with --insecure-registry
  (kargakis@users.noreply.github.com)
- Use p12-encoded certs on OS X (jliggitt@redhat.com)
- Initialize image by using struct literal (kargakis@users.noreply.github.com)
- *AccessReviews (deads@redhat.com)
- pass authorizer/attributebuilder pair into master (deads@redhat.com)
- Update the custom tagger and builder to provide OpenShift ldflags
  (sdodson@redhat.com)
- put templates in correct dir for install registry script (bparees@redhat.com)
- UPSTREAM: properly handle mergo map versus value rules: 4416
  (deads@redhat.com)
- Add missing Requires (nakayamakenjiro@gmail.com)
- Explain why Stop is called like that (michaliskargakis@gmail.com)
- Allow setting final logout uri (jliggitt@redhat.com)
- tolerate missing roles (deads@redhat.com)
- update in-container steps to setup registry properly (bparees@redhat.com)
- Making race an option for sh scripts (dmcphers@redhat.com)
- Fixing test coverage reporting (dmcphers@redhat.com)
- Generate client configs for nodes, provider-qualify and add groups to certs
  (jliggitt@redhat.com)
- add resourceName to policy (deads@redhat.com)
- Use LabelSelector in overview to associate pods to a service
  (jforrest@redhat.com)
- Issue 865: Fixed build integration tests. (maszulik@redhat.com)
- Validate image repository (michaliskargakis@gmail.com)
- Fix off-by-1 error (jliggitt@redhat.com)
- Support namespace in path for requesting k8s api from web console
  (jforrest@redhat.com)
- Bug 1191824 - Fixing typo (bleanhar@redhat.com)
- Require network when starting openshift-master (jolamb@redhat.com)
- Add project settings page and show quota and limit ranges for the project
  (jforrest@redhat.com)
- Attempt to manipulate images path conditionally (sdodson@redhat.com)
- Change ORIGIN_OAUTH_* env vars to OPENSHIFT_OAUTH_* (jliggitt@redhat.com)
- Bug 1191354 - must save username to .kubeconfig correctly
  (contact@fabianofranz.com)
- Use kubernetes user.Info interface (jliggitt@redhat.com)
- add policy watches (deads@redhat.com)
- Update the web console to request k8s api on v1beta3 (jforrest@redhat.com)
- Use Warningf instead of Warning so formatting works (nagy.martin@gmail.com)
- Bug 1190095 - useless entry "nameserver <nil>" is in docker container
  resolv.conf (bleanhar@redhat.com)
- deploymentconfigs permission typo (deads@redhat.com)
- Removed all Google copyrights leftovers (maszulik@redhat.com)
- e2e formatting (deads@redhat.com)
- tighten bootstrap policy (deads@redhat.com)
- Change references from alpha to beta release (sdodson@redhat.com)
- Default session secret to unknowable value (jliggitt@redhat.com)
- Make token lifetimes configurable (jliggitt@redhat.com)
- Allow denying a prompted OAuth grant (jliggitt@redhat.com)
- Make user header configurable (jliggitt@redhat.com)
- remove deny and negations (deads@redhat.com)
- Use chown for build-in-docker.sh output binaries (nagy.martin@gmail.com)
- Make sure vagrant development environment works well with new docker-io
  (marek.goldmann@gmail.com)
- move cleanup to its own section (bparees@redhat.com)
- Comment on redirecting to login on 0 codes (jliggitt@redhat.com)
- Add better instructions around using vagrant (dmcphers@redhat.com)
- Prevent browsers from prompting to send bogus client certs
  (jliggitt@redhat.com)
- add edge terminated route to sample app (pweil@redhat.com)
- make more intelligent kubeconfig merge (deads@redhat.com)
- Register used mime types (jliggitt@redhat.com)
- use tags from imagerepos when constructing new builds (bparees@redhat.com)
- Update example project json (jliggitt@redhat.com)
- Check SELinux labels when building in docker (nagy.martin@gmail.com)
- Various idiomatic fixes throughout the repo (michaliskargakis@gmail.com)
- Check for unspecified port once (michaliskargakis@gmail.com)
- Generate shorter tags when building release tars (ccoleman@redhat.com)
- Update start help (ccoleman@redhat.com)
- Tweak the flag for --images to indicate applies to master and node
  (ccoleman@redhat.com)
- Improve the default osc help page (ccoleman@redhat.com)
- Display more information when an app is automatically created
  (ccoleman@redhat.com)
- make remove-group from role check all bindings (deads@redhat.com)
- Improve error handling and logging for builds (cewong@redhat.com)
- UPSTREAM: Use name from server when displaying create/update
  (ccoleman@redhat.com)
- Correlate deployed pods with their deployments (ironcladlou@gmail.com)
- Remove comments from minified HTML (jliggitt@redhat.com)
- Preserve newlines in html (jliggitt@redhat.com)
- Add upgrade-aware HTTP proxy (agoldste@redhat.com)
- Handle multiple builder matches in generate command (cewong@redhat.com)
- OAuth api printers (jliggitt@redhat.com)
- Set user fullname correctly, initialize identity mappings fully
  (jliggitt@redhat.com)
- Set KUBECONFIG path for openshift-node (sdodson@redhat.com)
- Sort ports for service generation and select first port (cewong@redhat.com)
- Enable `osc new-app` and simplify some of the rough edges for launch
  (ccoleman@redhat.com)
- Command for displaying global options is "osc options" in help
  (contact@fabianofranz.com)
- Delete token on logout (jliggitt@redhat.com)
- Syntax consistency between help templates (contact@fabianofranz.com)
- Fixes base command reference (osc || openshift cli) in help
  (contact@fabianofranz.com)
- RPMs: Fix upgrades for the tuned profile (sdodson@redhat.com)
- Better footer messages in help (contact@fabianofranz.com)
- Fix help line breaks (contact@fabianofranz.com)
- Remove the usage from the list of available commands in help
  (contact@fabianofranz.com)
- modify .kubeconfig (deads@redhat.com)
- Basic structure for osc login (contact@fabianofranz.com)
- fix scripts http url to https (bparees@redhat.com)
- Start node with --kubeconfig should use master host from config file
  (jforrest@redhat.com)
- Bug 1189390 - fix project selector so it gets re-rendered after project list
  changes (jforrest@redhat.com)
- Switch to localStorage (jliggitt@redhat.com)
- Fix image change trigger imageRepo matching (ironcladlou@gmail.com)
- Show latest deployment in deploy config describe (ironcladlou@gmail.com)
- Update documentation to use 'osc create' consistently (mfojtik@redhat.com)
- Tighten header styles inside tiles (jliggitt@redhat.com)
- Only warn when chcon fails (ccoleman@redhat.com)
- Restore logic to disregard resources in pod diff (ironcladlou@gmail.com)
- UPSTREAM: Register nodes that already exist statically (ccoleman@redhat.com)
- Only allow session auth to be used for a single auth flow
  (jliggitt@redhat.com)
- Remove aliases and options command from cli template
  (contact@fabianofranz.com)
- make ovs-simple from openshift-sdn the default networking solution for
  vagrant (rchopra@redhat.com)
- Use certs in vagrant mutli node environment. (mrunalp@gmail.com)
- Nuke the default usage section from client templates
  (contact@fabianofranz.com)
- Introduces "osc options" to list global options (contact@fabianofranz.com)
- Custom template for cli and osc, hide global options
  (contact@fabianofranz.com)
- fix service select for frontend (bparees@redhat.com)
- Ignore .pyc files (sdodson@redhat.com)
- OpenShift should set a client UserAgent on all calls (ccoleman@redhat.com)
- Add OAuth login to console (jliggitt@redhat.com)
- Set a default user agent on all client.Client calls (ccoleman@redhat.com)
- remove use of osc namespace command (bparees@redhat.com)
- create template file for image repos (bparees@redhat.com)
- add skip build flag support for test target (pweil@redhat.com)
- Remove references to openshift/kubernetes (dmcphers@redhat.com)
- use Status.DockerImageRepository instead of DockerImageRepository
  (bparees@redhat.com)
- Reorganize command line code and move app-gen under experimental
  (cewong@redhat.com)
- Slightly increase the wait for hack/test-cmd.sh (ccoleman@redhat.com)
- WIP - osc new-app with argument inference (ccoleman@redhat.com)
- [WIP] Simple generation flow for an application based on source
  (cewong@redhat.com)
- Simple source->build->deploy generation (ccoleman@redhat.com)
- remove guestbook link (bparees@redhat.com)
- Add missing step when testing k8s rebase (jhonce@redhat.com)
- Bug 1188933 - Missing es5-dom-shim causes CustomEvent polyfill to fail in IE
  (jforrest@redhat.com)
- Resource round tripping has been fixed and new fields added to pod
  (ccoleman@redhat.com)
- Master takes IP instead of string (ccoleman@redhat.com)
- Use RESTMapper scopes for registering resources (ccoleman@redhat.com)
- UPSTREAM: Disable UIs for Kubernetes and etcd (ccoleman@redhat.com)
- UPSTREAM: Disable auto-pull when tag is "latest" (ccoleman@redhat.com)
- UPSTREAM: spf13/cobra help display separate groups of flags
  (contact@fabianofranz.com)
- UPSTREAM: Add 'release' field to raven-go (ccoleman@redhat.com)
- bump(github.com/GoogleCloudPlatform/kubernetes):72ad4f12bd7408a6f75e6a0bf37b3
  440e165bdf4 (ccoleman@redhat.com)
- hack/end-to-end should terminate jobs (ccoleman@redhat.com)
- Set volume dir SELinux context if possible (agoldste@redhat.com)
- Typo on master.go around pullIfNotPresent (ccoleman@redhat.com)
- Update HACKING.md with the release push instructions (ccoleman@redhat.com)
- Bash is the worst programming language ever invented (ccoleman@redhat.com)
- Restore CORS outside of go-restful (ccoleman@redhat.com)
- use start-build instead of curl (bparees@redhat.com)
- Add CONTEXT_DIR support for sti-image-builder image (mfojtik@redhat.com)
- Generate openshift service on provision (dmcphers@redhat.com)
- Expose two new flags on master --images and --latest-images
  (ccoleman@redhat.com)
- Create an openshift/origin-pod image (ccoleman@redhat.com)
- check for error on missing docker file (bparees@redhat.com)
- remove guestbook example (bparees@redhat.com)
- Refactor css, variablize more values and restructure label filter markup
  (sgoodwin@redhat.com)
- Adding tests for help consistency to test-cmd.sh (contact@fabianofranz.com)
- UPSTREAM: special command "help" must be aware of context
  (contact@fabianofranz.com)
- better description of output to field (bparees@redhat.com)
- experimental policy cli (deads@redhat.com)
- UPSTREAM: need to make sure --help flags is registered before calling pflag
  (contact@fabianofranz.com)
- move kubernetes capabilities to server start (patrick.hemmer@gmail.com)
- Add --check option to run golint and gofmt in ./hack/build-in-docker.sh
  (mfojtik@redhat.com)
- Add retry logic to recreate deployment strategy (ironcladlou@gmail.com)
- Very simple authorizing proxy for Kubernetes (ccoleman@redhat.com)
- Unify authorization logic into a more structured form (ccoleman@redhat.com)
- User registry should transform server errors (ccoleman@redhat.com)
- UPSTREAM: Handle case insensitive node names and squash logging
  (ccoleman@redhat.com)
- UPSTREAM: Use new resource builder in kubectl update #3805
  (nagy.martin@gmail.com)
- remove unnecessary rest methods (deads@redhat.com)
- UPSTREAM: add flag to manage $KUBECONFIG files: #4053, bugzilla 1188208
  (deads@redhat.com)
- Add ./hack/build-in-docker.sh script (mfojtik@redhat.com)
- Fix Go version checking in verify-gofmt (mfojtik@redhat.com)
- Use $http (jliggitt@redhat.com)
- sample-app docs: update for TLS, namespace, context (lmeyer@redhat.com)
- Removed "Additional Help Topics" section from help template
  (contact@fabianofranz.com)
- Use our own templates to cli help and usage (contact@fabianofranz.com)
- UPSTREAM: spf13/cobra help display separate groups of flags
  (contact@fabianofranz.com)
- add missing reencrypt validations (pweil@redhat.com)
- Label filtering widget in the web console, styles by @sg00dwin
  (jforrest@redhat.com)
- remove unnecessary labels from sample imagerepos (bparees@redhat.com)
- Add shortcuts for build configs and deployment configs (ccoleman@redhat.com)
- Remove kubecfg, expose kubectl in its place (ccoleman@redhat.com)
- bump(github.com/docker/docker):211513156dc1ace48e630b4bf4ea0fcfdc8d9abf
  (cewong@redhat.com)
- Update project display name for sample app (decarr@redhat.com)
- UPSTREAM: typos (contact@fabianofranz.com)
- ignore local .kubeconfig (deads@redhat.com)
- Improve /oauth/token/request page (jliggitt@redhat.com)
- Compile haproxy with generic CPU instructions (sdodson@redhat.com)
- Fix multi minion setup (dmcphers@redhat.com)
- policy authorizer (deads@redhat.com)
- policy client (deads@redhat.com)
- policy storage (deads@redhat.com)
- policy types (deads@redhat.com)
- Fix the Vagrant network setup (lhuard@amadeus.com)
- Remove empty log files and use a slightly different process kill method
  (ccoleman@redhat.com)
- Refactor to match upstream master changes (ccoleman@redhat.com)
- Better debug output in deployment_config_controller (ccoleman@redhat.com)
- Adapt to upstream changes for cache.Store (ccoleman@redhat.com)
- UPSTREAM: Relax validation around annotations (ccoleman@redhat.com)
- UPSTREAM: Support GetByKey so EventStore can de-dup (ccoleman@redhat.com)
- UPSTREAM: Add 'release' field to raven-go (ccoleman@redhat.com)
- UPSTREAM: Allow namespace short to be set (ccoleman@redhat.com)
- UPSTREAM: api registration right on mux makes it invisible to container
  (contact@fabianofranz.com)
- UPSTREAM: Disable auto-pull when tag is "latest" (ccoleman@redhat.com)
- UPSTREAM: Disable UIs for Kubernetes and etcd (ccoleman@redhat.com)
- bump(github.com/GoogleCloudPlatform/kubernetes):e335e2d3e26a9a58d3b189ccf41ce
  b3770d1bfa9 (ccoleman@redhat.com)
- Escape helper echo in rebase-kube (ccoleman@redhat.com)
- only kill and remove k8s managed containers (bparees@redhat.com)
- Gofmt whitespace flaw (ccoleman@redhat.com)
- Helper function for rebase output (ccoleman@redhat.com)
- UPSTREAM: Disable UIs for Kubernetes and etcd (ccoleman@redhat.com)
- UPSTREAM: Disable auto-pull when tag is "latest" (ccoleman@redhat.com)
- Godeps: update tags to be accurate (ccoleman@redhat.com)
- Properly version Kubernetes and OpenShift binaries (ccoleman@redhat.com)
- Connect the node to the master via and a built in client
  (ccoleman@redhat.com)
- Rebase fixes (ccoleman@redhat.com)
- Fix flaky travis by limiting parallel builds (ccoleman@redhat.com)
- UPSTREAM: api registration right on mux makes it invisible to container
  (contact@fabianofranz.com)
- UPSTREAM: Allow namespace short to be set (ccoleman@redhat.com)
- bump(github.com/GoogleCloudPlatform/kubernetes):e0acd75629ec29bde764bcde29367
  146ae8b389b (jhonce@redhat.com)
- pkill on test-end-to-end.sh must be sudo (ccoleman@redhat.com)
- Set user UID in session (jliggitt@redhat.com)
- Implement deployment rollback CLI support (ironcladlou@gmail.com)
- Make file references relative in generated .kubeconfig files
  (jliggitt@redhat.com)
- Add ability to retrieve userIdentityMapping (jliggitt@redhat.com)
- Add "Oauth" prefix to oauth types (jliggitt@redhat.com)
- Register internal OAuth API objects correctly (jliggitt@redhat.com)
- Allow bower to run as root (dmcphers@redhat.com)
- Vagrantfile: improve providers and usability/readability (lmeyer@redhat.com)
- UPSTREAM: resolve relative paths in .kubeconfig (deads@redhat.com)
- Pin haproxy to 1.5.10 (sdodson@redhat.com)
- 'osc' should be symlinked in the openshift/origin Docker image
  (ccoleman@redhat.com)
- Split master and node packaging (sdodson@redhat.com)
- create test project for e2e (deads@redhat.com)
- Fix the Vagrant network setup (lhuard@amadeus.com)
- stop "OpenShift will terminate as soon as a panic occurs" from spamming
  during e2e (deads@redhat.com)
- Add asset server hostname to cert, generate cert without ports
  (jliggitt@redhat.com)
- Integration tests should let master load its own API (ccoleman@redhat.com)
- Build openshift-web-console oauth client (jliggitt@redhat.com)
- Externalize and doc auth config (jliggitt@redhat.com)
- Auto grant, make oauth sessions short, handle session decode failures
  (jliggitt@redhat.com)
- Prettify token display page (jliggitt@redhat.com)
- Add login template (jliggitt@redhat.com)
- Rename fedora image (dmcphers@redhat.com)
- refactor build interfaces (bparees@redhat.com)
- Allow to customize env variables for STI Build strategy (mfojtik@redhat.com)
- Don't cache the generated config.js or it won't pick up changes in startup
  options (jforrest@redhat.com)
- Makes 'config' set of commands experimental (contact@fabianofranz.com)
- Fix guestbook example to not collide with 'frontend' service
  (mfojtik@redhat.com)
- Convert Config to kapi.List{} and fix Template to use runtime.Object{}
  (mfojtik@redhat.com)
- UPSTREAM(ae3f10): Ensure the ptr is pointing to reflect.Slice in ExtractList
  (mfojtik@redhat.com)
- UPSTREAM(e7df8a): Fix ExtractList to support extraction from generic
  api.List{} (mfojtik@redhat.com)
- osc binary not present for Mac or Windows, windows needs .exe
  (ccoleman@redhat.com)
- Exposes 'osc config' to manage .kubeconfig files (contact@fabianofranz.com)
- Skip client cert gen if it exists (jliggitt@redhat.com)
- Skip server cert gen if exists and is valid (jliggitt@redhat.com)
- Copy openshift binary in the tar (ccoleman@redhat.com)
- Switch default instance size (dmcphers@redhat.com)
- Set public kubernetes master when starting kube (jliggitt@redhat.com)
- Allow images to be tagged in hack/push-release.sh (ccoleman@redhat.com)
- add server arg to osc command to support remote masters (pweil@redhat.com)
- Add option to unionauth to fail on error, fail on invalid or expired bearer
  tokens (jliggitt@redhat.com)
- Update bindata.go (decarr@redhat.com)
- Update ui code to not use project.metadata.namespace (decarr@redhat.com)
- Align project with upstream resources that exist outside of namespace
  (decarr@redhat.com)
- fix public-ip for node-sdn (rchopra@redhat.com)
- Fix bindata.go for the less partials split (jforrest@redhat.com)
- Change box url and name back (dmcphers@redhat.com)
- router TLS (pweil@redhat.com)
- Make insert key configurable (dmcphers@redhat.com)
- Make the provider configs optional (dmcphers@redhat.com)
- Splitting .less into partials and refactor of code. Including openshift-icon
  font set for now. (sgoodwin@redhat.com)
- bump(github.com/smarterclayton/go-
  dockerregistryclient):3b6185cb3ac3811057e317dcff91f36eef17b8b0
  (ccoleman@redhat.com)
- kill openshift process during e2e (deads@redhat.com)
- resolve osapi endpoint to be configured as upstream to resolve 406
  (jcantril@redhat.com)
- Config Generator should not return raw errors via the REST API
  (ccoleman@redhat.com)
- Fix vagrant single vm environment (pmorie@gmail.com)
- Enable authentication, add x509 cert auth, anonymous auth
  (jliggitt@redhat.com)
- Separate OAuth and API muxes, pass authenticator into master
  (jliggitt@redhat.com)
- Add x509 authenticator (jliggitt@redhat.com)
- Add groups to userinfo (jliggitt@redhat.com)
- Allow panics to be reported to Sentry (ccoleman@redhat.com)
- UPSTREAM: Allow panics and unhandled errors to be reported to external
  targets (ccoleman@redhat.com)
- UPSTREAM: Add 'release' field to raven-go (ccoleman@redhat.com)
- bump(github.com/getsentry/raven-go):3fd636ed242c26c0f55bc9ee1fe47e1d6d2d77f7
  (ccoleman@redhat.com)
- Add missing error assignments (michaliskargakis@gmail.com)
- Add profiling tools to the OpenShift binary (ccoleman@redhat.com)
- Add instructions to ignore vboxnet interfaces on the host.
  (mrunalp@gmail.com)
- Move registry install function to a reusable spot (ccoleman@redhat.com)
- Remove unused api target from Makefile comments (vvitek@redhat.com)
- add dns recommendations (bparees@redhat.com)
- Fix bug #686 (pmorie@gmail.com)
- Lock webcomponents version (jliggitt@redhat.com)
- bump(github.com/pkg/profile):c795610ec6e479e5795f7852db65ea15073674a6
  (ccoleman@redhat.com)
- Use correct client config to run token cmd (jliggitt@redhat.com)
- Update routing readme and script to set up TLS (jliggitt@redhat.com)
- Separate asset bind and asset public addr (jliggitt@redhat.com)
- provide an environment switch to choose ovs-simple as the overlay network for
  the cluster (rchopra@redhat.com)
- start: provide + use flags for public API addresses (lmeyer@redhat.com)
- No need to redoc k8s in origin (dmcphers@redhat.com)
- Review comments 2 - Pass Codec through and return error on setBuildEnv
  (ccoleman@redhat.com)
- Disable race detection on test-integration because of #731
  (ccoleman@redhat.com)
- Crash on Panic when ENV var set (ccoleman@redhat.com)
- asset server: change bind addr (lmeyer@redhat.com)
- delete large log files before archiving to jenkins (bparees@redhat.com)
- Bug: Build logs could be accessed only when the pod phase was running
  (j.hadvig@gmail.com)
- packaging: put runtime data to /var/lib/origin (ttomecek@redhat.com)
- packaging: remove invalid options in /etc/sysconf/os (ttomecek@redhat.com)
- WIP - Template updates (ccoleman@redhat.com)
- More flexibility to test-cmd and test-end-to-end (ccoleman@redhat.com)
- Remove the need to load deployments from config_generator
  (ccoleman@redhat.com)
- Allow more goroutines to exit during test cases with RunUntil
  (ccoleman@redhat.com)
- Return the most recently updated deployment config after PUT
  (ccoleman@redhat.com)
- Cleanup integration tests (ccoleman@redhat.com)
- Add "from" object reference to both ImageChangeTriggers (ccoleman@redhat.com)
- Support service variable substitution in docker registry variable
  (ccoleman@redhat.com)
- Use Status.DockerImageRepository from CLI (ccoleman@redhat.com)
- Check for an ImageRepositoryMapping with metadata/name before DIR
  (ccoleman@redhat.com)
- Review comments (ccoleman@redhat.com)
- When creating build, lookup "to" field if specified (ccoleman@redhat.com)
- Define "to" and "dockerImageReference" as new fields on BuildOutput
  (ccoleman@redhat.com)
- UPSTREAM: Add RunUntil(stopCh) to reflector and poller to allow termination
  (ccoleman@redhat.com)
- UPSTREAM: Expose validation.ValidateLabels for reuse (ccoleman@redhat.com)
- Disable other e2e tests (ccoleman@redhat.com)
- UPSTREAM: Use ExtractObj instead of ExtractList in Kubelet
  (ccoleman@redhat.com)
- Introduce deployment rollback API (ironcladlou@gmail.com)
- design policy (deads@redhat.com)
- Enable privileged capabilities in apiserver (ironcladlou@gmail.com)
- Wireframes of label filter interface states event-based user actions
  (sgoodwin@redhat.com)
- run custom, docker builds in e2e (bparees@redhat.com)
- Updating HACKING doc with more detailed information about Kubernetes rebases
  (contact@fabianofranz.com)
- Remove hard-coded resourceVersion values from build watches
  (maszulik@redhat.com)
- Make vagrant run in http for now (jliggitt@redhat.com)
- Default --master scheme to match --listen (jliggitt@redhat.com)
- Rebuild to pick up new webcomponents (jliggitt@redhat.com)
- Fix internal token request with TLS (jliggitt@redhat.com)
- Remove flag hard-coding (pmorie@gmail.com)
- Send events from the master (ccoleman@redhat.com)
- Don't hard-code resourceVersion in watches (ironcladlou@gmail.com)
- Enable TLS (jliggitt@redhat.com)
- UPSTREAM: Allow changing global default server hostname (jliggitt@redhat.com)
- Exclude .git and node_modules from test search (ironcladlou@gmail.com)
- UPSTREAM: Use CAFile even when cert/key is not specified, allow client config
  to take cert data directly (jliggitt@redhat.com)
- Typo in deployment controller factory (pmorie@gmail.com)
- Remove yaml from all object types (mfojtik@redhat.com)
- Router doc json cleanup (pmorie@gmail.com)
- Make OSC use non-interactive auth loading, fix flag binding
  (jliggitt@redhat.com)
- UPSTREAM: make kubectl factory flag binding optional (jliggitt@redhat.com)
- Fix docker build with context directory (cewong@redhat.com)
- docs: Filling in some initial model descriptions (lmeyer@redhat.com)
- docs: *_model.adoc => .md (lmeyer@redhat.com)
- Make hack/build-go.sh create symlinks for openshift (pmorie@gmail.com)
- UPSTREAM: bump(github.com/jteeuwen/go-bindata):
  f94581bd91620d0ccd9c22bb1d2de13f6a605857 (jliggitt@redhat.com)
- UPSTREAM: Disable UIs for Kubernetes and etcd (ccoleman@redhat.com)
- Refactor to match changes upstream (mfojtik@redhat.com)
- Refactor to match changes upstream (contact@fabianofranz.com)
- UPSTREAM: api registration right on mux makes it invisible to container
  (contact@fabianofranz.com)
- bump(github.com/GoogleCloudPlatform/kubernetes):21b661ecf3038dc50f75d345276c9
  cf460af9df2 (contact@fabianofranz.com)
- In case of failure, wait and restart the openshift-node service
  (marek.goldmann@gmail.com)
- Pull in hawtio-core-navigation and build console nav around it. Styles and
  theming by @sg00dwin (jforrest@redhat.com)
- fix namespacing so sample works again (bparees@redhat.com)
- Fix gofmt detection (jliggitt@redhat.com)
- add missing quotes to privileged (bparees@redhat.com)
- Require docker-io 1.3.2 or later. Remove -devel FIXME (sdodson@redhat.com)
- Support `GET /imageRepositoryTags/<name>:<tag>` (ccoleman@redhat.com)
- Properly version Docker image metadata sent to the API (ccoleman@redhat.com)
- UPSTREAM: Expose TypeAccessor for objects without metadata
  (ccoleman@redhat.com)
- Update end-to-end to use new registry pattern (ccoleman@redhat.com)
- Depend on docker-io (sdodson@redhat.com)
- Tolerate missing build logs in cancel-build (jliggitt@redhat.com)
- Constants are mismatched on BuildTriggerType (ccoleman@redhat.com)
- Move systemd unit and sysconfig files to rel-eng (sdodson@redhat.com)
- ImageRepository lookup should check the OpenShift for <namespace>/<name>
  (ccoleman@redhat.com)
- UPSTREAM: Disable auto-pull when tag is "latest" (ccoleman@redhat.com)
- Initial pass at getting tito set up for release engineering purposes
  (sdodson@redhat.com)
- Update sample app README now that cors-allowed-origins option isn't required
  for embedded web console (jforrest@redhat.com)
- Move specification for api version for web console into console code.  Add
  127.0.0.1 to default cors list. (jforrest@redhat.com)
- Web console talks to master over configured master host/port and embedded web
  console allowed by default in CORS list (jforrest@redhat.com)
- Bug 1176815 - Improve error reporting for build-log (mfojtik@redhat.com)
- Update README with simpler commands (ccoleman@redhat.com)
- Minor whitespace cleanup (ccoleman@redhat.com)
- Ensure tests shut themselves down, and fix race in imagechange test
  (ccoleman@redhat.com)
- Add Delete methods to various Image objects (ccoleman@redhat.com)
- Update the Makefile to run all tests (ccoleman@redhat.com)
- One last path fix (matthicksj@gmail.com)
- Fixing openshift path (matthicksj@gmail.com)
- Updating to use Makefile and updating path (matthicksj@gmail.com)
- use privileged containers for builds and docker registry (bparees@redhat.com)
- docs: place for k8s/os model descriptions (lmeyer@redhat.com)
- deep copy when creating build from buildconfig (bparees@redhat.com)
- Push the new STI images into configured output imageRepository
  (mfojtik@redhat.com)
- Add the hawtio-extension-service as a dependency (jforrest@redhat.com)
- Fixed bug: the master was advertising its internal IP when running the dev
  cluster through Vagrant (marko.luksa@gmail.com)
- ignore tag duplicaiton with multiple runs of e2e tests (akostadi@redhat.com)
- make sure errors don't abort tear down (akostadi@redhat.com)
- add image change trigger example to json (bparees@redhat.com)
- correct end-to-end test executable name in HACKING doc (akostadi@redhat.com)
- Fixed SELinux and firewalld commands for temporary disabling.
  (hripps@redhat.com)
- Modified with changes from review 1 (hripps@redhat.com)
- Delete built images after pushing them to registry (cewong@redhat.com)
- Added info about necessary SELinux & firewalld setup (hripps@redhat.com)
- git is also required, otherwise `go get` does not work (akostadi@redhat.com)
- Do not tag with GIT ref when the SOURCE_REF is not set (sti-image-builder)
  (mfojtik@redhat.com)
- Fixed unpacking of sti in sti-image-builder (mfojtik@redhat.com)
- introduce image change build trigger logic (bparees@redhat.com)
- force the docker registry ip to be constant (bparees@redhat.com)
- Refactor data service to better handle resourceVersion, unsubscribe, context
  specific callback lists, etc... (jforrest@redhat.com)
- Added STI image builder image (mfojtik@redhat.com)
- Rewrite and re-scope deployment documentation (ironcladlou@gmail.com)
- update readme to work with web console (bparees@redhat.com)
- Double error print in the OpenShift command (ccoleman@redhat.com)
- Implement deployments without Deployment (ironcladlou@gmail.com)
- Add generic webhook payload to versioned types (cewong@redhat.com)
- Updated STI builder according to latest STI version (maszulik@redhat.com)
- bump(github.com/openshift/source-to-
  image/pkg/sti):5813879841b75b7eb88169d3265a0560fdf50b12 (maszulik@redhat.com)
- correct awk command to get correct endpoint (jialiu@redhat.com)
- correct awk command to get correct endpoint (jialiu@redhat.com)
- Fixing sti url (dmcphers@redhat.com)
- Fixing typos (dmcphers@redhat.com)
- added setup documentation when using the docker container and the sample app
  (erikmjacobs@gmail.com)
- tweaked getting started readme (erikmjacobs@gmail.com)
- Pull in the hawtio-core framework into the console (jforrest@redhat.com)
- Updated STI builder according to latest STI version (maszulik@redhat.com)
- bump(github.com/openshift/source-to-
  image/pkg/sti):48cf2e985b571ddc67cfb84a59a339be38b98a81 (maszulik@redhat.com)
- Make grunt hostname/port configurable (ironcladlou@gmail.com)
- Vagrantfile: accommodate empty lines in ~/.awscred (jolamb@redhat.com)
- ssl_fc_has_sni is meant to work post ssl termination, use req_ssl_sni to
  directly lookup the extacted sni from the map. (rchopra@redhat.com)
- Added --parameters and --value options for kubectl#process command
  (mfojtik@redhat.com)
- OPENSHIFT_NUM_MINIONS env var was not honored (marko.luksa@gmail.com)
- add instructions for insecure registry config (bparees@redhat.com)
- Update README.md (scitronpousty@gmail.com)
- Specifically add github.com/docker/docker/pkg/units (ccoleman@redhat.com)
- Refactor to match upstream (ccoleman@redhat.com)
- UPSTREAM: Disable UIs for Kubernetes and etcd (ccoleman@redhat.com)
- bump(github.com/GoogleCloudPlatform/kubernetes):6624b64f440a0f10a8d9ca401c3b1
  40f1bf2f945 (ccoleman@redhat.com)
- Cache control assets with ETag based on commit (jforrest@redhat.com)
- Kube make clean doesn't work without Docker (ccoleman@redhat.com)
- Update cli.md (jasonkuhrt@me.com)
- Issue 253 - Added STI scripts location as part of the STI strategy
  (maszulik@redhat.com)
- fix template test fixture (rajatchopra@gmail.com)
- fix template : redis-master label missing. issue#573 (rajatchopra@gmail.com)
- Enable html5 mode in the console (jforrest@redhat.com)
- Improve example validation and add template fixtures for example data
  (ccoleman@redhat.com)
- Allow resources posted to /templateConfigs to omit name (ccoleman@redhat.com)
- Template parameter processing shouldn't return errors for unrecognized types
  (ccoleman@redhat.com)
- Fix errors in guestbook template.json (ccoleman@redhat.com)
- Return typed errors from template config processing (ccoleman@redhat.com)
- Set uid, creation timestamp using standard utility from kube
  (decarr@redhat.com)
- Remove debug statement from master.go (ccoleman@redhat.com)
- Templates don't round trip (ccoleman@redhat.com)
- fix interface typo (bparees@redhat.com)
- Ensure namespace will be serialized in proper location when moving to path
  param (decarr@redhat.com)
- Update bindata to match upstream dependencies (jforrest@redhat.com)
- bump(github.com/spf13/cobra):e1e66f7b4e667751cf530ddb6e72b79d6eeb0235
  (maszulik@redhat.com)
- UPSTREAM: kubectl delete command: adding labelSelector (vvitek@redhat.com)
- Proposal for capabilities (jforrest@redhat.com)
- Update nav with labels (sgoodwin@redhat.com)
- Incorrect path argument for Golint (j.hadvig@gmail.com)
- Update bindata to match an updated dependency (jforrest@redhat.com)
- Reintroduced Vagrant version sensitivity (hripps@redhat.com)
- Updated Vagrantfile to reflect config processing changes as of Vagrant 1.7.1
  (hripps@redhat.com)
- Clean up (j.hadvig@gmail.com)
- V3 console navigation structure and interaction (sgoodwin@redhat.com)
- Remove API docs and replace with link to Swagger UI (ccoleman@redhat.com)
- Support the swagger API from OpenShift master (ccoleman@redhat.com)
- UPSTREAM: Take HandlerContainer as input to master to allow extension
  (ccoleman@redhat.com)
- Fix 'openshift cli' longDesc string arg reference (vvitek@redhat.com)
- Router refactor (pmorie@gmail.com)
- fix #551, make the service ip range private (deads@redhat.com)
- Cancel new builds. Update client logic. (maria.nita.dn@gmail.com)
- Cleanup OpenShift CLI (ccoleman@redhat.com)
- test-cmd should use raw 'osc' calls (ccoleman@redhat.com)
- Make test-end-to-end more readable (ccoleman@redhat.com)
- Golint is broken on Mac (ccoleman@redhat.com)
- tweaks to handle new kubernetes, kick travis again (deads@redhat.com)
- bump(github.com/GoogleCloudPlatform/kubernetes):3910b2d6e18759b3a9a6920c7f3d0
  ccd122df7f9 (deads@redhat.com)
- Move from go 1.4rc2 to 1.4 release (jordan@liggitt.net)
- helper script to fix registry ip (bparees@redhat.com)
- Rename STIBuildStrategy.BuildImage to Image (mfojtik@redhat.com)
- Refactoring router.go to handle errors. Improving code coverage - Add port
  forwarding from 8080 to localhost:8080 on VirtualBox - Refactoring router.go
  to handle errors. Improving code coverage. - Adding port forwarding from 80
  to localhost:1080 on VirtualBox, and comments on how to test locally -
  Applying refactor change to controller/test/test_router.go - Fixing
  identation - Fixing unit tests - Organizing imports - Merge (akram@free.fr)
- Fix project description in example and console to work as an annotation
  (jforrest@redhat.com)
- fix auth packages, kick travis yet again (deads@redhat.com)
- add cli challenge interaction, kick travis again (deads@redhat.com)
- Added documentation for custom build (mfojtik@redhat.com)
- cancel-build fails if no pod was assigned (deads@redhat.com)
- Initial addition of CustomBuild type (mfojtik@redhat.com)
- Improve error reporting (vvitek@redhat.com)
- add instructions to edit registry service ip (bparees@redhat.com)
- Add go1.4 to travis (jliggitt@redhat.com)
- EventQueue should provide events for replaced state (pmorie@gmail.com)
- Exit install-assets.sh when the command fails (mfojtik@redhat.com)
- make openshift run on new kubernetes (deads@redhat.com)
- UPSTREAM: go-restful, fix race conditions https://github.com/emicklei/go-
  restful/pull/168 (deads@redhat.com)
- UPSTREAM: Add util.Until (ccoleman@redhat.com)
- bump(github.com/GoogleCloudPlatform/kubernetes):b614f22935df36f8c1d6bd3c5c9fe
  850e79fd729 (deads@redhat.com)
- Add a Status field on ImageRepository (ccoleman@redhat.com)
- Various Go style fixes (mfojtik@redhat.com)
- increase retries to account for slow systems (bparees@redhat.com)
- Add command to cancel build     - Add flag to print build logs  - Add flag to
  restart build     - Test command (maria.nita.dn@gmail.com)
- Add PodManager to build resource, to handle pod delete and create
  (maria.nita.dn@gmail.com)
- Add resource flag and status for cancelling build (maria.nita.dn@gmail.com)
- always dump build log to build.log (bparees@redhat.com)
- Router sharding proposal 2/2 (pmorie@gmail.com)
- Router sharding proposal 1/2 (pweil@redhat.com)
- Simplify webhook URL display (cewong@redhat.com)
- Add strategy and revision output to Build describer (cewong@redhat.com)
- Marks 'openshift kube' as deprecated (contact@fabianofranz.com)
- Removes 'openshift kubectl' in favor of 'openshift cli', 'kubectl' set as an
  alias (contact@fabianofranz.com)
- Exposes 'openshift cli', removing the osc binary for now
  (contact@fabianofranz.com)
- Basic structure for the end-user client command (osc)
  (contact@fabianofranz.com)
- Install assets more quietly (mfojtik@redhat.com)
- Add '-m' option to verify-golint to check just modified files
  (mfojtik@redhat.com)
- Bug 1170545 - Error about deployment not found (j.hadvig@gmail.com)
- ALL_CAPS to CamelCase (j.hadvig@gmail.com)
- Array declaration change (j.hadvig@gmail.com)
- receiver name should not be an underscore (j.hadvig@gmail.com)
- Reciever name consistency (j.hadvig@gmail.com)
- Removing underscore from method name (j.hadvig@gmail.com)
- Use DeploymentStrategy instead of recreate.DeploymentStrategy
  (j.hadvig@gmail.com)
- replacing 'var += 1' with 'var++' (j.hadvig@gmail.com)
- error strings should not end with punctuation (j.hadvig@gmail.com)
- Fix variable names (j.hadvig@gmail.com)
- Fix panic in webhook printing (mfojtik@redhat.com)
- Refactor printing of values in kubectl describe (mfojtik@redhat.com)
- Add missing Update, Create and Delete methods to Project client
  (mfojtik@redhat.com)
- Remove namespace from Project client and Describer (mfojtik@redhat.com)
- fix service spec camel case (pweil@redhat.com)
- Fix #286: Fix Config with nil Labels (vvitek@redhat.com)
- bump(github.com/openshift/source-to-image):
  1075509c5833e58fda33f03ce07307d7193d74f4 (maszulik@redhat.com)
- Simplify code to get rid variable shadowing (maszulik@redhat.com)
- replace build trigger with build command (bparees@redhat.com)
- Fix failed tests (mfojtik@redhat.com)
- getUrl -> getURL (mfojtik@redhat.com)
- Rename grant.GrantFormRenderer to grant.FormRenderer (mfojtik@redhat.com)
- Fix variable names (Url -> URL, client_id -> clientID, etc...)
  (mfojtik@redhat.com)
- Replace ALL_CAPS in basicauth_test with camel case (mfojtik@redhat.com)
- Use 'template.Processor' instead of 'template.TemplateProcessor'
  (mfojtik@redhat.com)
- Replace errors.New(fmt.Sprintf(...)) with fmt.Errorf(...)
  (mfojtik@redhat.com)
- Get rid of else from an if block when it contains return (mfojtik@redhat.com)
- Ascii should be ASCII (mfojtik@redhat.com)
- webhookUrl should be webhookURL (mfojtik@redhat.com)
- NoDefaultIP should be ErrNoDefaultIP (mfojtik@redhat.com)
- Fixed godoc in server/start (mfojtik@redhat.com)
- Remove else from env() func (mfojtik@redhat.com)
- Fixed godoc for origin/auth package (mfojtik@redhat.com)
- Fixed missing godoc in cmd/infra package (mfojtik@redhat.com)
- Added missing godoc and obsolete notice (mfojtik@redhat.com)
- Added missing godoc (mfojtik@redhat.com)
- Fixed if block that ends with a return in serialization test
  (mfojtik@redhat.com)
- Added godoc for multimapper constant (mfojtik@redhat.com)
- Rename haproxy.HaproxyRouter to haproxy.Router (mfojtik@redhat.com)
- Added Project describer (mfojtik@redhat.com)
- Added client for Project (mfojtik@redhat.com)
- Replace Description with Annotations in Project (mfojtik@redhat.com)
- Fixed wrong User() and UserIdentityMappings in Fake client
  (mfojtik@redhat.com)
- Added kubectl Describer for Origin objects (mfojtik@redhat.com)
- Rename config.mergeMaps() as util.MergeInto() (vvitek@redhat.com)
- UPSTREAM: Add Labels and Annotations to MetadataAccessor (vvitek@redhat.com)
- UPSTREAM: meta_test should not depend on runtime.TypeMeta (vvitek@redhat.com)
- update to use new openshift jenkins image tag (bparees@redhat.com)
- allow unbound skip_image_cleanup variable (bparees@redhat.com)
- Porting manual build-trigger to kubectl (j.hadvig@gmail.com)
- Gzip assets (jliggitt@redhat.com)
- Add dependency on github.com/daaku/go.httpgzip
  (3f59977b58c61991f5ed3670bbd141937d808b06) (jliggitt@redhat.com)
- Simplify asset test, keep line breaks in css and js (jliggitt@redhat.com)
- Change AddRoute signature to use ep structs, factor out functions for
  testability, add unit tests for said functions (pweil@redhat.com)
- add jenkins sample (bparees@redhat.com)
- Fixup the gofmt'ed bindata.go file (jforrest@redhat.com)
- UPSTREAM: Fixes #458 - retrieval of Docker container stats from cadvisor
  (jimmidyson@gmail.com)
- bump(github.com/google/cadvisor): 89088df70eca64cf9d6b9a23a3d2bc21a30916d6
  (jimmidyson@gmail.com)
- Stop deployment controllers during integration tests (ccoleman@redhat.com)
- UPSTREAM: Add util.Until (ccoleman@redhat.com)
- Prepare for nested commands (ccoleman@redhat.com)
- bump(github.com/spf13/cobra): b825817fc0fc59fc1657bc8202204a04ae3d679d
  (ccoleman@redhat.com)
- Added docs/cli.md describing the kubectl interface (mfojtik@redhat.com)
- Fixed typos, mixing comments and removed unused method (maszulik@redhat.com)
- Fix documentation to use kubectl instead of kubecfg (mfojtik@redhat.com)
- Replace kubecfg with kubectl in e2e test (mfojtik@redhat.com)
- Fix incorrect namespace for origin kubectl commands (mfojtik@redhat.com)
- Fixed typo in kubectl build-log (mfojtik@redhat.com)
- Cleanup godoc / tests for router, event queue (pmorie@gmail.com)
- Add SKIP_IMAGE_CLEANUP env variable for E2E test (mfojtik@redhat.com)
- Fixed test-service.json fixture to be v1beta2 (mfojtik@redhat.com)
- Switch test-cmd.sh to use kubectl instead of kubecfg (mfojtik@redhat.com)
- Use ResourceFromFile to get namespace and data (mfojtik@redhat.com)
- Refactor router controller unit tests (pmorie@gmail.com)
- link debugging guide from other docs (bparees@redhat.com)
- Correct urlVars field name (j.hadvig@gmail.com)
- UPSTREAM: Fix pluralization in RESTMapper when kind ends with 'y' (#2569)
  (mfojtik@redhat.com)
- Define printer for Origin objects in kubectl (mfojtik@redhat.com)
- Added TODOs and NOTE into Config#Apply (mfojtik@redhat.com)
- Added 'openshift kubectl build-logs' command (mfojtik@redhat.com)
- Added 'openshift kubectl process' command (mfojtik@redhat.com)
- Added 'openshift kubectl apply' command (mfojtik@redhat.com)
- Initial import for pkg/cmd/kubectl into origin (mfojtik@redhat.com)
- Added MultiRESTMapper into pkg/api/meta (mfojtik@redhat.com)
- create a troubleshooting guide (bparees@redhat.com)
- print invalid responses (bparees@redhat.com)
- Added ./hack/verify-golint.sh command (mfojtik@redhat.com)
- Make install-assets.sh work outside TRAVIS (jliggitt@redhat.com)
- Initial implementation of a project's overview in the web console
  (jforrest@redhat.com)
- Add hack script for pythia tool (decarr@redhat.com)
- Add EventQueue and refactor LBManager to use client/cache (pmorie@gmail.com)
- bump(github.com/jteeuwen/go-bindata):f94581bd91620d0ccd9c22bb1d2de13f6a605857
  (jforrest@redhat.com)
- Include required fields on AccessToken type, always serialize Items fields
  (jliggitt@redhat.com)
- Manual build trigger (j.hadvig@gmail.com)
- Rework client.Interface to match upstream (maszulik@redhat.com)
- vagrant-libvirt support (inecas@redhat.com)
- Fix vagrant rsync (inecas@redhat.com)
- Remove omitempty annotation from Items property in list types
  (cewong@redhat.com)
- Add build namespace to built image environment (cewong@redhat.com)
- Use upstream ParseWatchResourceVersion (agoldste@redhat.com)
- ImageRepository fixes (agoldste@redhat.com)
- Add auth-proxy-test (deads@redhat.com)
- Manual build launch (cewong@redhat.com)
- Add watch method for build configs (cewong@redhat.com)
- Adding port forwarding from 80 to localhost:1080 on VirtualBox, fixing indent
  and comments on how to test locally (akram@free.fr)
- Ref mailing list (ccoleman@redhat.com)
- bump(github.com/openshift/source-to-image)
  81ea479a67c279351661653c2a40f9428d4e259b (bparees@redhat.com)
- update registery ip references to reflect new default services
  (bparees@redhat.com)
- Change Identity.Name to Identity.UserName (jliggitt@redhat.com)
- Correlate Pods to Deployments during Recreate (ironcladlou@gmail.com)
- add union auth request handler (deads@redhat.com)
- Go builds are under /local (decarr@redhat.com)
- Fix project example after rebase (decarr@redhat.com)
- update readme to use generic webhook (bparees@redhat.com)
- add endpoint for displaying token (deads@redhat.com)
- Fix error message in generic webhook (cewong@redhat.com)
- Make auth interfaces more flexible (jliggitt@redhat.com)
- update registry config to be more self-sufficient (bparees@redhat.com)
- Fix Build API JSON tags for BuildStrategy (cewong@redhat.com)
- Fix deployment image change trigger bug (ironcladlou@gmail.com)
- fix checking for nil body on generic webhook invocation (bparees@redhat.com)
- minor change to install script to allow passing id. Moved router readme to
  docs. Updated readme for HA setup and documented DNS RR. (pweil@redhat.com)
- Fix ID -> Name in printers (pmorie@gmail.com)
- Kube rebase (3/3) (soltysh@gmail.com)
- Kube rebase (2/3) (mfojtik@redhat.com)
- Kube rebase (1/3) (contact@fabianofranz.com)
- bump(github.com/GoogleCloudPlatform/kubernetes):
  97cb1fa2df8b57be5ceaae290e02872f291b7b7e (contact@fabianofranz.com)
- Update to use uncompressed bindata for easier diffs (jforrest@redhat.com)
- bump(github.com/jteeuwen/go-bindata):bbd0c6e271208dce66d8fda4bc536453cd27fc4a
  (jforrest@redhat.com)
- Fixing typos (dmcphers@redhat.com)
- Log streaming logic update (j.hadvig@gmail.com)
- Add --net=host option for simplicity in Docker steps. (ccoleman@redhat.com)
- Docker run command was wrong (ccoleman@redhat.com)
- Refactor build config to use triggers (cewong@redhat.com)
- Add NoCache flag to docker builds (cewong@redhat.com)
- bump(github.com/openshift/source-to-image)
  53a27ab4cc8c6abfe84904a6503490bbf0bf7abb (bparees@redhat.com)
- Fix API references (cewong@redhat.com)
- router e2e integration (pweil@redhat.com)
- Deployment proposal: add detail to image spec (pmorie@gmail.com)
- Strengthen deploy int test assertions (ironcladlou@gmail.com)
- [BZ1163618] Add missing user agent to error message (jcantril@redhat.com)
- Clean up and add tests to the Recreate strategy (ironcladlou@gmail.com)
- Better sudoer seding (dmcphers@redhat.com)
- Use constants for deployment annotations (ironcladlou@gmail.com)
- add user identity mapping provisioning (deads@redhat.com)
- Fix build watch resource kind (cewong@redhat.com)
- Update deployment API examples and docs (ironcladlou@gmail.com)
- Fix naming of openshift/origin-deployer image (ironcladlou@gmail.com)
- Implement deployments with pods (ironcladlou@gmail.com)
- comments round 1 (deads@redhat.com)
- gofmt (pweil@redhat.com)
- test case and remove newline from glog statements (pweil@redhat.com)
- Do not delete the entire structure when just an alias is removed. bz1157388
  (rchopra@redhat.com)
- Godoc fix (j.hadvig@gmail.com)
- typo fixed (deads@redhat.com)
- Remove obsolete API examples (maria.nita.dn@gmail.com)
- Add command to run gofmt for bad formatted Go files (maria.nita.dn@gmail.com)
- Check all expected files have an existent JSON file. Update list of expected
  files (maria.nita.dn@gmail.com)
- Generate API doc for new examples (maria.nita.dn@gmail.com)
- Validate API examples. Rename files (maria.nita.dn@gmail.com)
- Switch back to gp2 volumes (dmcphers@redhat.com)
- Fix typos (dmcphers@redhat.com)
- add token option to clientcmd (deads@redhat.com)
- Fix WORKDIR typo in Dockerfile (ironcladlou@gmail.com)
- Fix typo (dmcphers@redhat.com)
- use token from command line (deads@redhat.com)
- update openshift path (bparees@users.noreply.github.com)
- Remove extra binaries (ccoleman@redhat.com)
- Move standalone commands into the pkg/cmd pattern (ccoleman@redhat.com)
- Add utility functions for commands that connect to a master
  (ccoleman@redhat.com)
- Move start logic into its own method and return errors. (ccoleman@redhat.com)
- router readme and install script (pweil@redhat.com)
- Fixing typo in URL (abhgupta@redhat.com)
- Use a standard working dir for Docker images (ccoleman@redhat.com)
- OpenShift in a container README (ccoleman@redhat.com)
- Minor changes to test artifacts (pmorie@gmail.com)
- WIP: deployments proposal (pmorie@gmail.com)
- Enhance deployment list and watch APIs (ironcladlou@gmail.com)
- bump(github.com/openshift/source-to-image)
  add9ff4973d949b4c82fb6a217e6919bb6e6be23 (cewong@redhat.com)
- Add grant approval, scope.Add, tests (jliggitt@redhat.com)
- Add a flag to support clean STI builds to the STIBuildStrategy
  (cewong@redhat.com)
- Convert builder images to use go (cewong@redhat.com)
- Fix deployment pod template comparison (cewong@redhat.com)
- rework sample to use STI build type (bparees@redhat.com)
- [DEVEXP 391] Add generic webhook to trigger builds manually
  (jcantril@redhat.com)
- Document test-go.sh, add option to show coverage for all tests
  (jliggitt@redhat.com)
- Make deploymentConfigs with config change triggers deploy automatically when
  created (pmorie@gmail.com)
- Generate html coverage info (jliggitt@redhat.com)
- Mention commit message format for bumping Godeps (vvitek@redhat.com)
- make use of common mock objects (deads@redhat.com)
- Updated pre-pulled images (soltysh@gmail.com)
- Fixed buildLogs (soltysh@gmail.com)
- Reorganize the template pkg, make it match upstream patterns
  (vvitek@redhat.com)
- More flaky test fixes (agoldste@redhat.com)
- UPSTREAM: Support PUT returning 201 on Create, kick travis
  (ccoleman@redhat.com)
- kubernetes cherry-pick 2074 and 2140 (deads@redhat.com)
- gofmt etcd_test.go and fix broken route test after change to argument type
  (pweil@redhat.com)
- unit test for route watches (pweil@redhat.com)
- fix issues with route watches returning 404 and 500 errors (pweil@redhat.com)

* Fri Sep 18 2015 Scott Dodson <sdodson@redhat.com> 0.2-9
- Rename from openshift -> origin
- Symlink /var/lib/origin to /var/lib/openshift if /var/lib/openshift exists

* Wed Aug 12 2015 Steve Milner <smilner@redhat.com> 0.2-8
- Master configs will be generated if none are found when the master is installed.
- Node configs will be generated if none are found when the master is installed.
- Additional notice file added if config is generated by the RPM.
- All-In-One services removed.

* Wed Aug 12 2015 Steve Milner <smilner@redhat.com> 0.2-7
- Added new ovs script(s) to file lists.

* Wed Aug  5 2015 Steve Milner <smilner@redhat.com> 0.2-6
- Using _unitdir instead of _prefix for unit data

* Fri Jul 31 2015 Steve Milner <smilner@redhat.com> 0.2-5
- Configuration location now /etc/origin
- Default configs created upon installation

* Tue Jul 28 2015 Steve Milner <smilner@redhat.com> 0.2-4
- Added AEP packages

* Mon Jan 26 2015 Scott Dodson <sdodson@redhat.com> 0.2-3
- Update to 21fb40637c4e3507cca1fcab6c4d56b06950a149
- Split packaging of openshift-master and openshift-node

* Mon Jan 19 2015 Scott Dodson <sdodson@redhat.com> 0.2-2
- new package built with tito

* Fri Jan 09 2015 Adam Miller <admiller@redhat.com> - 0.2-2
- Add symlink for osc command line tooling (merged in from jhonce@redhat.com)

* Wed Jan 07 2015 Adam Miller <admiller@redhat.com> - 0.2-1
- Update to latest upstream release
- Restructured some of the golang deps  build setup for restructuring done
  upstream

* Thu Oct 23 2014 Adam Miller <admiller@redhat.com> - 0-0.0.9.git562842e
- Add new patches from jhonce for systemd units

* Mon Oct 20 2014 Adam Miller <admiller@redhat.com> - 0-0.0.8.git562842e
- Update to latest master snapshot

* Wed Oct 15 2014 Adam Miller <admiller@redhat.com> - 0-0.0.7.git7872f0f
- Update to latest master snapshot

* Fri Oct 03 2014 Adam Miller <admiller@redhat.com> - 0-0.0.6.gite4d4ecf
- Update to latest Alpha nightly build tag 20141003

* Wed Oct 01 2014 Adam Miller <admiller@redhat.com> - 0-0.0.5.git6d9f1a9
- Switch to consistent naming, patch by jhonce

* Tue Sep 30 2014 Adam Miller <admiller@redhat.com> - 0-0.0.4.git6d9f1a9
- Add systemd and sysconfig entries from jhonce

* Tue Sep 23 2014 Adam Miller <admiller@redhat.com> - 0-0.0.3.git6d9f1a9
- Update to latest upstream.

* Mon Sep 15 2014 Adam Miller <admiller@redhat.com> - 0-0.0.2.git2647df5
- Update to latest upstream.
