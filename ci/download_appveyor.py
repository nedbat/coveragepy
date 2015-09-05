"""Use the Appveyor API to download Windows artifacts."""

import os
import os.path
import pprint
import zipfile

import requests


def make_auth_headers():
    with open("ci/appveyor.token") as f:
        token = f.read().strip()

    headers = {
        'Authorization': 'Bearer {}'.format(token),
    }
    return headers


def get_project_build(account, project):
    url = "https://ci.appveyor.com/api/projects/{account}/{project}".format(account=account, project=project)
    response = requests.get(url, headers=make_auth_headers())
    return response.json()


def download_latest_artifacts(account, project):
    build = get_project_build(account, project)
    jobs = build['build']['jobs']
    print "Build {0[build][version]}, {1} jobs: {0[build][message]}".format(build, len(jobs))
    for job in jobs:
        name = job['name'].partition(':')[2].split(',')[0].strip()
        print "  {0}: {1[status]}, {1[artifactsCount]} artifacts".format(name, job)

        url = "https://ci.appveyor.com/api/buildjobs/{jobid}/artifacts".format(jobid=job['jobId'])
        response = requests.get(url, headers=make_auth_headers())
        artifacts = response.json()

        for artifact in artifacts:
            type = artifact['type']
            filename = artifact['fileName']
            print "    {0}".format(filename)

            url = "https://ci.appveyor.com/api/buildjobs/{jobid}/artifacts/{filename}".format(jobid=job['jobId'], filename=filename)
            download_url(url, filename, make_auth_headers())

            if type == "Zip":
                unpack_zipfile(filename)
                os.remove(filename)


def download_url(url, filename, headers):
    dirname, _ = os.path.split(filename)
    if dirname and not os.path.exists(dirname):
        os.makedirs(dirname)
    response = requests.get(url, headers=headers, stream=True)
    if response.status_code == 200:
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(16*1024):
                f.write(chunk)


def unpack_zipfile(filename):
    with open(filename, 'rb') as fzip:
        z = zipfile.ZipFile(fzip)
        for name in z.namelist():
            print "      extracting {}".format(name)
            z.extract(name)


if __name__ == "__main__":
    download_latest_artifacts("nedbat", "coveragepy")
