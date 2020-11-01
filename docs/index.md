REST Testing Tool (py3resttest)
==========

This is a clone of pyresttest to support py3 and optimized lot of functionality. 


# Table of Contents

- [What Is It?](#what-is-it)
- [Status](#status)
- [Installation](#installation)
- [Sample Test](#sample-test)
- [Examples](#examples)
- [Installation](#installation)
- [How Do I Use It?](#how-do-i-use-it)
	- [Running A Simple Test](#running-a-simple-test)
	- [Using JSON Validation](#using-json-validation)
	- [Interactive Mode](#interactive-mode)
	- [Verbose Output](#verbose-output)
- [Other Goodies](#other-goodies)
- Basic Test Set Syntax
	- [Import example](#import-example)
	- [Url Test](#url-test-with-timeout)
	- [Custom HTTP Options (special curl settings)](#custom-http-options-special-curl-settings)
	- [Syntax Limitations](#syntax-limitations)
- [RPM-based installation](#rpm-based-installation)
- [Project Policies](#project-policies)
- [FAQ](#faq)
- [Feedback and Contributions](#feedback-and-contributions)

# What Is It?
- A REST testing and API microbenchmarking tool
- Tests are defined in basic YAML or JSON config files, no code needed
- Minimal dependencies (pycurl, pyyaml), making it easy to deploy on-server for smoketests/healthchecks
- Supports [generate/extract/validate](advanced_guide.md) mechanisms to create full test scenarios with workflow
- Returns exit codes on failure, to slot into automated configuration management/orchestration tools (also supplies parseable logs)
- Logic is written and [extensible](extensions.md) in Python

# Status

**Python 3.5+ Support** 
 
Apache License, Version 2.0

[Changelog](CHANGELOG.md) shows the past and present, [milestones](https://abhijo89-to.github.io/py3resttest/milestones) show the future roadmap.

* The changelog will also show features/fixes currently merged to the master branch but not released to PyPi yet (pending installation tests across platforms). 

# Installation
Works on Linux or Mac with Python 3.5+ 

**First we need to install package python-pycurl:**
* Ubuntu/Debian: (sudo) `apt-get install python3-pycurl`
* CentOS/RHEL: (sudo) `yum install python3-pycurl`
* Alpine: (sudo) `apk add curl-dev`
* Mac: *don't worry about it*
* Other platforms: *unsupported.*  You *may* get it to work by installing pycurl & pyyaml manually.
*This is needed because the pycurl dependency may fail to install by pip. 

**It is easy to install the latest release by pip:**
(sudo) `pip install resttest3`

**If pip isn't installed, we'll want to install it first:**
If that is not installed, we'll need to install it first:
* Ubuntu/Debian: (sudo) `apt-get install python3-pip`
* CentOS/RHEL: (sudo) `yum install python3-pip`
* Mac OS X with homebrew: `brew install python3`  (it's included)
* Or with just python installed: `wget https://bootstrap.pypa.io/get-pip.py && sudo python3 get-pip.py`

**Releases occur every month, if you want to use unreleased features, it's easy to install from source:**

*See the [Change Log](CHANGELOG.md) for feature status.*

```shell
git clone https://github.com/abhijo89-to/py3resttest.git
cd py3resttest
sudo python setup.py install
```

The master branch tracks the latest; it is unit tested, but less stable than the releases (the 'stable' branch tracks tested releases).


## Troubleshooting Installation

Almost all installation issues are due to problems with PyCurl and PyCurl's native libcurl bindings. 
It is easy to check if PyCurl is installed correctly:

`python -c 'import pycurl'`

If this returns correctly, pycurl is installed, if you see an ImportError or similar, it isn't.
You may also verify the pyyaml installation as well, since that can fail to install by pip in rare circumstances.

### Error installing by pip
`__main__.ConfigurationError: Could not run curl-config: [Errno 2] No such file or directory`

This is caused by libcurl not being installed or recognized: first install pycurl using native packages as above.  Alternately, try installing just the libcurl libraries:

- On Ubuntu/Debian: `sudo apt-get install libcurl4-openssl-dev`
- On CentOS/RHEL: `yum install libcurl-devel`


# Sample Test
**This will check that APIs accept operations, and will smoketest an application**
```yaml
---
- config:
    - testset: "Basic tests"
- test: 
    - name: "Basic get"
    - url: "/api/person/"
- test: 
    - name: "Get single person"
    - url: "/api/person/1/"
- test: 
    - name: "Delete a single person, verify that works"
    - url: "/api/person/1/"
    - method: 'DELETE'
- test: # create entity by PUT
    - name: "Create/update person"
    - url: "/api/person/1/"
    - method: "PUT"
    - body: '{"first_name": "Gaius","id": 1,"last_name": "Baltar","login": "gbaltar"}'
    - headers: {'Content-Type': 'application/json'}
    - validators:  # This is how we do more complex testing!
        - compare: {header: content-type, comparator: contains, expected:'json'}
        - compare: {jsonpath_mini: 'login', expected: 'gbaltar'}  # JSON extraction
        - compare: {raw_body:"", comparator:contains, expected: 'Baltar' }  # Tests on raw response
- test: # create entity by POST
    - name: "Create person"
    - url: "/api/person/"
    - method: "POST"
    - body: '{"first_name": "William","last_name": "Adama","login": "theadmiral"}'
    - headers: {Content-Type: application/json}
  ```
# Examples
* The [Quickstart](quickstart.md) should be *everyone's* starting point
* Here's a [really good example](miniapp-extract-validate.yaml) for how to create a user and then do tests on it.  
  - This shows how to use extraction from responses, templating, and different test types
* If you're trying to do something fancy, take a look at the [content-test.yaml](content-test.yaml).
  - This shows most kinds of templating & variable uses. It shows how to read from file, using a variable in the file path, and templating on its content!
* PyRestTest isn't limited to JSON; there's an [example for submitting form data](../examples/dummyapp-posting-forms.yaml)
* There's a [whole folder](../examples) of example tests to help get started



# How Do I Use It?
- The [Quickstart](quickstart.md) walks through common use cases
- Advanced features have [separate documentation](advanced_guide.md) (templating, generators, content extraction, complex validation).
- How to [extend PyRestTest](extensions.md) is its own document
- @BastienAr has created an [Atom editor package](https://atom.io/packages/language-pyresttest) for PyRestTest development (thank you!)

## Running A Simple Test

Run a basic test of the github API:

```shell
resttest3 https://api.github.com examples/github_api_smoketest.yaml
```

## Using JSON Validation

A simple set of tests that show how json validation can be used to check contents of a response.
Test includes both successful and unsuccessful validation using github API.

```shell
resttest3 https://api.github.com examples/github_api_test.yaml
```

(For help: pyresttest  --help )

## Interactive Mode
Same as the other test but running in interactive mode.

```shell
resttest3 https://api.github.com examples/github_api_test.yaml --interactive true --print-bodies true
```

## Verbose Output

```shell
resttest3 https://api.github.com examples/github_api_test.yaml --log debug
```


# Other Goodies
* Simple templating of HTTP request bodies, URLs, and validators, with user variables
* Generators to create dummy data for testing, with support for easily writing your own
* Sequential tests: extract info from one test to use in the next
* Import test sets in other test sets, to compose suites of tests easily
* Easy benchmarking: convert any test to a benchmark, by changing the element type and setting output options if needed
* Lightweight benchmarking: ~0.3 ms of overhead per request, and plans to reduce that in the future
* Accurate benchmarking: network measurements come from native code in LibCurl, so test overhead doesn't alter them
* Optional interactive mode for debugging and demos

# Basic Test Set Syntax
As you can see, tests are defined in [YAML](http://en.wikipedia.org/wiki/YAML) format.

There are 5 top level test syntax elements:
- *url:* a simple test, fetches given url via GET request and checks for good response code
- *test*: a fully defined test (see below)
- *benchmark*: a fully defined benchmark (see below)
- *config* or *configuration*: overall test configuration (timeout is the most common option)
- *import*: import another test set file so you Don't Repeat Yourself

## Import example
```yaml
---
# Will load the test sets from miniapp-test.yaml and run them
# Note that this will run AFTER the current test set is executed
# Also note that imported tests get a new Context: any variables defined will be lost between test sets
- import: examples/miniapp-test.yaml
```

Imports are intended to let you create top-level test suites that run many independent, isolated test scenarios (test sets).
They may also be used to create sample data or perform cleanup *as long as you don't rely on variables to store this information.*  For example, if one testset creates a user for a set of scenarios, tests that rely on that user's ID need to start by querying the API to get the ID.

## Url Test With Timeout
A simple URL test is equivalent to a basic GET test with that URL.
Also shows how to use the timeout option in testset config to descrease the default timeout from 10 seconds to 1. 

```yaml
---
- config:
    - testset: "Basic tests"
    - timeout: 1
- url: "/api/person/"  # This is a simple test
- test: 
    - url: "/api/person/"  # This does the same thing
```

## Custom HTTP Options (special curl settings)
For advanced cases (example: SSL client certs), sometimes you will want to use custom Curl settings that don't have a corresponding option in PyRestTest.  

This is easy to do: for each test, you can specify custom Curl arguments with 'curl_option_optionname.'  For this, 'optionname' is case-insensitive and the optionname is a [Curl Easy Option](http://curl.haxx.se/libcurl/c/curl_easy_setopt.html) with 'CURLOPT_' removed. 

For example, to follow redirects up to 5 times (CURLOPT_FOLLOWLOCATION and CURLOPT_MAXREDIRS):
```yaml
---
- test: 
    - url: "/api/person/1"
    - curl_option_followlocation: True
    - curl_option_maxredirs: 5  
```
Note that while option names are validated, *no validation* is done on their values.

## Syntax Limitations
* Whenever possible, the YAML configuration handler tries to convert variable types as needed.  We're all responsible adults, don't do anything crazy and it will play nicely.
* Only a handful of elements can use dynamic variables (URLs, headers, request bodies, validators) - there are plans to change this in the next few releases.
* The templating is quite limited (it's doing simple string subsitution). There are plans to improve this in the next few releases, but it isn't there yet.
* One caveat: *if you define the same element (example, URL) twice in the same enclosing element, the last value will be used.*  In order to preserve sanity, I use last-value wins.
* No support for "for-each" on requests/responses natively - this can be done via custom extensions, and may be available in the *distant* future but it's a while out.


# RPM-based installation

## Pure RPM-based install?
It's easy to build and install from RPM:

## Building the RPM:
```shell
python3 setup.py bdist_rpm  # Build RPM
find -iname '*.rpm'   # Gets the RPM name
```
### Installing from RPM
```shell
sudo yum localinstall my_rpm_name
sudo yum install PyYAML python3-pycurl  
```
- You need to install PyYAML & PyCurl manually because Python distutils can't translate python dependencies 
to RPM packages. 

## Building an RPM for RHEL 6/CentOS 6
You'll need to install rpm-build, and then it should work.

```shell
sudo yum install rpm-build
```

# Project Policies
* PyRestTest uses the Github flow
  - The master branch is an integration branch for mature features
  - Releases are cut periodically from master (every 3-6 months generally, or more often if breaking bugs are present) and released to PyPi
  - Feature development is done in feature branches and merged to master by PR when tested (validated by continuous integration in Jenkins)
  - The 'stable' branch tracks the last release, use this if you want to run PyRestTest from source
* [The changelog is here](CHANGELOG.md), this will show past releases and features merged to master for the next release but not released 
* Testing: tested on Ubuntu/python3 and CentOS /python3
* Releases occur every few months to [PyPi](https://pypi.org/project/py3resttest/#files) once a few features are ready to go
* PyRestTest uses [Semantic Versioning 2.0](http://semver.org/)
* **Back-compatibility is important! PyRestTest makes a strong effort to maintain command-line and YAML format back-compatibility since 1.0.**
  - [Extension method signatures](extensions.md) are maintained as much as possible. 
  - However, internal python implementations are subject to change.
  

# Feedback and Contributions
We welcome any feedback you have, including pull requests, reported issues, etc!

**For new contributors** there are a whole set of issues labelled with 
[help wanted](https://github.com/abhijo89-to/py3resttest/labels/help%20wanted) 
which are excellent starting points to offer a contribution! 

For instructions on how to set up a dev environment for PyRestTest, see [building.md](building.md).

**For pull requests to get easily merged, please:**
- Include unit tests (and functional tests, as appropriate) and verify that run_tests.sh passes
- Include documentation as appropriate
- Attempt to adhere to PEP8 style guidelines and project style

Bear in mind that this is largely a one-man, outside-of-working-hours effort at the moment, so response times will vary.  That said: every feature request gets heard, and even if it takes a while, all the reasonable features will get incorporated.  **If you fork the main repo, check back periodically... you may discover that the next release includes something to meet your needs and then some!**

# FAQ

## Why not pure-python tests?
- This is written for an environment where Python is not the sole or primary language
- **You totally can do pure-Python tests if you want!**  
    - [Extensions](extensions.md) provide a stable API for adding more complex functionality in python
    - All modules can be imported and used as libraries
    - Gotcha: the project is still young, so internal implementation may change often, much more than YAML features

## Why YAML and not XML/JSON?
- XML is extremely verbose and has many gotchas for parsing
- You **CAN use JSON for tests**, it's a subset of YAML. See [miniapp-test.json](examples/miniapp-test.json) for an example. 
- YAML tends to be the most concise, natural, and easy to write of these three options

## Does it do load tests?
- No, this is a separate niche and there are already many excellent tools to fill it
- Adding load testing features would greatly increase complexity
- But some form might come eventually!

## Why do you use PyCurl and not requests?
- Maybe eventually.  PyRestTest needs the low-level features of PyCurl for benchmarking, and benefits from its performance.  However we may eventually abstract some of the core testing features away to allow for pure-python execution
