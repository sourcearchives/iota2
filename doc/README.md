### Procedure to generate IOTA²'s documentation

1 - First you have to install some packages :
```bash
pip install Sphinx==1.7.6 sphinxcontrib-napoleon sphinx_rtd_theme numpydoc
```

2 - Create the sphinx environnement
```bash
# in order to get the environment variable IOTA2DIR
source iota2/scripts/install/prepare_env.sh

# documentation will be generate in MyIOTA2Doc
MyIOTA2Doc=$IOTA2DIR/doc/MyIOTA2Doc
mkdir -p $MyIOTA2Doc && cd $MyIOTA2Doc
sphinx-quickstart
```

3 - A list of questions will be asked. Answer the following:
```bash
Separate source and build directories (y/n) [n]: y
Name prefix for templates and static dir [_]: 
Project name: IOTA²
Author name(s):MyName
Project release []:
Project language [en]:
Source file suffix [.rst]:
Name of your master document (without suffix) [index]:
Do you want to use the epub builder (y/n) [n]:
autodoc: automatically insert docstrings from modules (y/n) [n]: y
doctest: automatically test code snippets in doctest blocks (y/n) [n]:
intersphinx: link between Sphinx documentation of different projects (y/n) [n]:
todo: write "todo" entries that can be shown or hidden on build (y/n) [n]:
coverage: checks for documentation coverage (y/n) [n]:
imgmath: include math, rendered as PNG or SVG images (y/n) [n]: y
mathjax: include math, rendered in the browser by MathJax (y/n) [n]: y
ifconfig: conditional inclusion of content based on config values (y/n) [n]:
viewcode: include links to the source code of documented Python objects (y/n) [n]: y
githubpages: create .nojekyll file to publish the document on GitHub pages (y/n) [n]:
Create Makefile? (y/n) [y]:
Create Windows command file? (y/n) [y]:
```

4 - Replace the directory "MyIOTA2Doc/source" by the git one
```bash
cp -r ../source/ ./
```

5 - Launch the html generation
```bash
make html
```

6 - Then you can vizualize the doc
```bash
firefox build/html/index.html
```
