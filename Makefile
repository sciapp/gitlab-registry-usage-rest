VERSION := $(shell python -c 'from gitlab_registry_usage_rest._version import __version__; print(__version__)')

upload: upload_docker upload_pypi

upload_docker: clean
	@[ "$$(git symbolic-ref -q HEAD)" == "refs/heads/master" ] || \
		{ echo "Uploading can only be done on the master branch."; exit 1; }
	CI_REPOSITORY_URL="https://github.com/sciapp/gitlab-registry-usage-rest" CI_COMMIT_REF_NAME="v$(VERSION)" envsubst < Dockerfile > Dockerfile_envsubst
	docker build -t sciapp/gitlab-registry-usage-rest:$(VERSION) -t sciapp/gitlab-registry-usage-rest:latest -f Dockerfile_envsubst .
	docker login
	docker push sciapp/gitlab-registry-usage-rest:$(VERSION)
	docker push sciapp/gitlab-registry-usage-rest:latest

upload_pypi: clean
	@[ "$$(git symbolic-ref -q HEAD)" == "refs/heads/master" ] || \
		{ echo "Uploading can only be done on the master branch."; exit 1; }
	python3 setup.py sdist && \
	python3 setup.py bdist_wheel && \
	twine upload dist/*

clean:
	rm -rf build dist *.egg-info Dockerfile_envsubst

.PHONY: clean upload upload_docker upload_pypi
