#!env make

        APP = ics-lint4
    VERSION = 0.1.0

# / ------ python stuff --------/ #
        REQ = requirements.txt
       DOCS = README.md
     RUNENV = venv
# / ------ python stuff --------/ #

all:    venv run

venv: $(REQ)
	python3 -m venv venv
	( . venv/bin/activate \
	&& test -f $(REQ) && python -m pip install --upgrade -r $(REQ) \
	&& python -m pip freeze > $(REQ).tmp )
	diff -qB $(REQ).tmp $(REQ) || cp $(REQ).tmp $(REQ)
	rm $(REQ).tmp

run: $(RUNENV)
	-( . $(RUNENV)/bin/activate && python $(APP).py )

clean:
	-rm -r $(RUNENV)
	-find -type d -name __pycache__ -exec rm -r '{}' ';'

