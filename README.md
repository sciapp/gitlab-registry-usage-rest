# GitLab-Registry-Usage-REST

## Introduction

*GitLab-Registry-Usage-REST* is a package that periodically collects repository information (names, tags, sizes) of a
GitLab registry server and offers the data via a secured [RESTful HAL](http://stateless.co/hal_specification.html) api.
For the initial authentication a LDAP server is needed. Subsequent queries are secured by *JSON Web Tokens* (JWT).

## Installation

The latest version can be obtained from PyPI:

```bash
pip install gitlab-registry-usage-rest
gitlab-registry-usage-rest --help
```

or from DockerHub:

```bash
docker run sciapp/gitlab-registry-usage-rest:latest --help
```

or from the AUR for Arch Linux based systems:

```bash
yay -S gitlab-registry-usage-rest
```

## Usage

*Gitlab-Registry-Usage-REST* needs a configuration file in order to run. The default path is
`/etc/gitlab_registry_usage_rest.conf` but can be altered with the `-c` command line switch. To get started, you can run

```bash
gitlab-registry-usage-rest --print-default-config
```

and edit this default configuration to fit your environment.

If you would like to use the docker repository, you can bind mount a local configuration file with the `-v` switch:

```bash
docker run -v "$(pwd)/gitlab_registry_usage_rest.conf:/etc/gitlab_registry_usage_rest.conf" sciapp/gitlab-registry-usage-rest:latest
```

**Note**: Docker expects an absolute path for the local configuration file.

The server offers these api endpoints:

- `/auth_token`: Accepts a request with basic auth (and valid LDAP credentials) and returns an auth token for further
  api usage. All other endpoints only accept requests with a valid `Bearer` authorization header:

  ```http
  Authorization: Bearer <token>
  ```

- `/repositories`: Lists attributes of the *repositories* collection. Currently, only the timestamp of the last data
  refresh is contained:

  ```json
  {
      "timestamp": 1521796487.7021387
  }
  ```

- `/repositories/<repository_name>`: Queries attributes of a specific repository:

  ```json
  {
      "name": "scientific-it-systems/administration/gitlab-registry-usage-rest",
      "size": 39899199,
      "disk_size": 39898911
  }
  ```

- `/repositories/<repository_name>/tags`: Endpoint for the collection of repository tags, currently without any content.

- `/repositories/<repository_name>/tags/<tag_name>`: Lists attributes of a tagged image stored in a repository:

  ```json
  {
      "name": "latest",
      "size": 39899199,
      "disk_size": 39898911
  }
  ```

Additionally, all api endpoints (except `/auth_token`) offer an `_embedded` and a `_links` attribute if requested with
the query string:

```
?embed=true&links=true
```

Instead of a boolean value, the embed key can also take an integer number to only request a specific level of embedded
resources.

Links can be used to easily navigate between related resources. Embedded resources are convenient to query a complete
hierarchy of resources with one GET request. Accordingly, the request

```
/repositories?embed=true
```

returns all resources at once.
