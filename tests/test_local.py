import pytest 
import datetime
import pdb
from neurocaas_contrib.local import NeuroCAASAutoScript,NeuroCAASImage,NeuroCAASLocalEnv,NeuroCAASRemoteEnv
from neurocaas_contrib.log import NeuroCAASDataStatus,NeuroCAASCertificate
from testpaths import get_dict_file 
import docker
import os

connection_ip = "54.157.238.198"

filepath = os.path.realpath(__file__)
testpath = os.path.dirname(filepath)
rootpath = os.path.dirname(testpath)

certpath = "s3://caiman-ncap-web/reviewers/results/job__caiman-ncap-web_1589650394/logs/certificate.txt"
## Check if we're running on a local machine or on a ci server. 

if get_dict_file() == "local":
    scriptdict = os.path.join(rootpath,"src/neurocaas_contrib/template_mats/example_scriptdict.json")
    scriptdict_env = os.path.join(rootpath,"src/neurocaas_contrib/template_mats/example_scriptdict_env.json")
    path = "/Users/taigaabe/anaconda3/bin"
elif get_dict_file() == "ci":
    scriptdict = os.path.join(rootpath,"src/neurocaas_contrib/template_mats/example_scriptdict_travis.json")
    scriptdict_env = os.path.join(rootpath,"src/neurocaas_contrib/template_mats/example_scriptdict_travis_env.json")
    path = "/home/runner/miniconda/bin"
else:
    assert 0,"Home directory not recognized for running tests."
    
client = docker.from_env()

## Check if we're running compute locally or on a docker remote host.  

if client.api.base_url == "http://localhost:2375":
    dockerhost = "remote"
else: 
    dockerhost = "local"


#@pytest.fixture(scope="class")
#def testinstance()

template = os.path.join(rootpath,"src/neurocaas_contrib/template_script.sh")

class Test_NeuroCAASImage(object):
    def test_NeuroCAASImage(self):
        nci = NeuroCAASImage()
    def test_NeuroCAASImage_assign_default_image(self):
        nci = NeuroCAASImage()
        image_tag = "hello-world:latest"
        nci.assign_default_image(image_tag)
        assert nci.image_tag == image_tag 
        assert nci.image == client.images.get(image_tag)
    def test_NeuroCAASImage_assign_default_image_noimage(self):
        nci = NeuroCAASImage()
        image_tag = "neurocaas/contrib"
        with pytest.raises(AssertionError):
            nci.assign_default_image(image_tag)
    def test_NeuroCAASImage_assign_default_container(self):
        nci = NeuroCAASImage()
        container = client.containers.create("hello-world:latest")
        cname = container.name
        nci.assign_default_container(cname)
        assert nci.container_name == cname
        assert nci.current_container == container
    def test_NeuroCAASImage_assign_default_container_exists(self):
        nci = NeuroCAASImage()
        container1 = client.containers.create("hello-world:latest")
        cname1 = container1.name
        container2 = client.containers.create("hello-world:latest")
        cname2 = container2.name
        nci.assign_default_container(cname1)
        nci.assign_default_container(cname2)
        assert nci.container_name == cname2
        assert nci.current_container == container2
        assert nci.container_history[container1.id] == container1
    def test_NeuroCAASImage_assign_default_container_noexists(self):
        nci = NeuroCAASImage()
        with pytest.raises(Exception):
            nci.assign_default_container("trash")
    def test_NeuroCAASImage_find_image(self):
        nci = NeuroCAASImage()
        nci.find_image("hello-world:latest")
    def test_NeuroCAASImage_find_image_noimage(self):
        nci = NeuroCAASImage()
        with pytest.raises(AssertionError):
            nci.find_image("neurocaas/contrib")
    def test_NeuroCAASImage_build_default_image(self):
        nci = NeuroCAASImage()
        nci.build_default_image()
    def test_NeuroCAASImage_setup_container(self):
        nci = NeuroCAASImage()
        nci.setup_container()
        try:
            container = nci.client.containers.get("neurocaasdevcontainer")
            container.remove(force=True)
        except:    
            pass

    def test_NeuroCAASImage_setup_container_env(self):
        ncle = NeuroCAASLocalEnv(os.path.join(testpath,"test_mats"))
        nci = NeuroCAASImage()
        nci.setup_container(env = ncle)
        try:
            container = nci.client.containers.get("neurocaasdevcontainer")
            container.remove(force=True)
        except:    
            pass

    def test_NeuroCAASImage_test_container(self):
        """This test can be a lot more sensitive and specific. This is just a basic test that the program finishes. 

        """
        nci = NeuroCAASImage()
        containername = "test_container"
        container = client.containers.run("neurocaas/contrib:base",command="/bin/bash",name=containername,detach=True,tty = True,stdin_open=True)
        nci.test_container(command='ls',container_name = containername)
        try:
            container = nci.client.containers.get(containername)
            container.remove(force=True)
        except:    
            pass

    def test_NeuroCAASImage_test_container_stopped(self):
        """This test can be a lot more sensitive and specific. This is just a basic test that the program finishes. 

        """
        nci = NeuroCAASImage()
        container = client.containers.create("hello-world:latest")
        cname = container.name
        nci.assign_default_container(cname)
        with pytest.raises(docker.errors.APIError):
            nci.test_container(command='ls')
        try:
            container = nci.client.containers.get(containername)
            container.remove(force=True)
        except:    
            pass

    def test_NeuroCAASImage_track_job_local(self): 
        if dockerhost is "remote":
            pytest.skip("can't run this test on remote host.")
        timestamp = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        job_id = f"job__{timestamp}"

        nci = NeuroCAASImage()
        ncle = NeuroCAASLocalEnv(os.path.join(testpath,"test_mats/test_analysis"))
        container = client.containers.run(image = nci.image_tag,command = "ls",detach = True)
        datastatus = NeuroCAASDataStatus("s3://dummy_path",container)
        certificate = NeuroCAASCertificate("s3://dummy_path")
        nci.track_job(ncle,datastatus,certificate,job_id)

    def test_NeuroCAASImage_track_job_remote(self): 
        if dockerhost is "local":
            pytest.skip("can't run this test on local host.")
        timestamp = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        job_id = f"job__{timestamp}"

        nci = NeuroCAASImage()
        ncle = NeuroCAASLocalEnv(os.path.join(testpath,"test_mats/test_analysis"))
        container = client.containers.run(image = nci.image_tag,command = "ls",detach = True)
        datastatus = NeuroCAASDataStatus("s3://dummy_path",container)
        certificate = NeuroCAASCertificate("s3://dummy_path")
        nci.track_job(ncle,datastatus,certificate,job_id)

    def test_NeuroCAASImage_run_analysis_local_host(self):
        if dockerhost is "remote": 
            pytest.skip("can't run this test on remote host.")
        nci = NeuroCAASImage()
        ncle = NeuroCAASLocalEnv(os.path.join(testpath,"test_mats"))
        nci.run_analysis("ls",ncle)

    def test_NeuroCAASImage_run_analysis_remote_host(self):
        remote_path = "/home/ubuntu/test_mats"
        remote_host = connection_ip
        remote_username = "ubuntu"
        keypath = "/Users/taigaabe/.ssh/id_rsa_remote_docker"
        if dockerhost is "local": 
            pytest.skip("can't run this test on local host.")
        nci = NeuroCAASImage()
        ncre = NeuroCAASRemoteEnv(os.path.join(testpath,"test_mats"),remote_path,remote_host,remote_username,keypath)
        nci.run_analysis("ls",ncre)

    def setup_method(self,test_method):
        pass
    def teardown_method(self,test_method):
        client.containers.prune()

class Test_NeuroCAASLocalEnv(object):
    def test_NeuroCAASLocalEnv(self):
        ncle = NeuroCAASLocalEnv(os.path.join(testpath,"test_mats"))

    @pytest.mark.xfail
    def test_NeuroCAASLocalEnv_create_volume(self):
        assert 0

    @pytest.mark.xfail
    def test_NeuroCAASLocalEnv_config_io_path(self):
        assert 0

class Test_NeuroCAASRemoteEnv(object):
    def test_NeuroCAASRemoteEnv(self):
        remote_path = "/home/ubuntu/test_mats"
        remote_host = connection_ip
        remote_username = "ubuntu"
        keypath = "/Users/taigaabe/.ssh/id_rsa_remote_docker"
        if dockerhost is "local": 
            pytest.skip("can't run this test on local host.")
        ncre = NeuroCAASRemoteEnv(os.path.join(testpath,"test_mats"),remote_path,remote_host,remote_username,keypath)

class Test_NeuroCAASAutoScript(object):
    def test_NeuroCAASAutoScript(self):
        ncas = NeuroCAASAutoScript(scriptdict,template)

    def test_NeuroCAASAutoScript_add_dlami(self):
        ncas = NeuroCAASAutoScript(scriptdict_env,template)
        ncas.add_dlami()
        ncas.scriptlines[-1] == "source .dlamirc"

    def test_NeuroCAASAutoScript_append_conda_path_command(self):
        ncas = NeuroCAASAutoScript(scriptdict,template)
        command = ncas.append_conda_path_command(path)
        assert command == f"export PATH=\"{path}:$PATH\""

    def test_NeuroCAASAutoScript_check_conda_env(self):
        ncas = NeuroCAASAutoScript(scriptdict,template)
        assert ncas.check_conda_env("neurocaas")

    def test_NeuroCAASAutoScript_add_conda_env(self):
        ncas = NeuroCAASAutoScript(scriptdict_env,template)
        ncas.add_conda_env(path = path)
        assert ncas.scriptlines[-2] == f"export PATH=\"{path}:$PATH\" \n" 
        assert ncas.scriptlines[-1] == f"conda activate neurocaas \n"

    def test_NeuroCAASAutoScript_write_new_script(self):
        ncas = NeuroCAASAutoScript(scriptdict,template)
        script_path = os.path.join(testpath,"test_mats/test_write_new_script.sh")
        ncas.write_new_script(script_path)
        with open(script_path,"r") as f1:
            with open(template,"r") as f2:
                f1r = f1.readlines()
                f2r = f2.readlines()
                assert len(f1r) == len(f2r)
                for r1,r2 in zip(f1r,f2r):
                    assert r1 == r2

    def test_NeuroCAASAutoScript_check_dirs(self):
        ncas = NeuroCAASAutoScript(scriptdict,template)
        ncas.check_dirs()
        refpaths = ["mkdir -p \"/home/ubuntu/datastore/\"", "mkdir -p \"/home/ubuntu/outstore/results/\""]

        for s in ncas.scriptlines[-2:]:
            assert s in refpaths


