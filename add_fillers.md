# Project initialization

python main.py init Docs

# Add objects with versions

python main.py add Welcome --version 1.0.0 --section "API Methods" --audience amateur
python main.py add Welcome --version 1.0.1 --section "API Methods" --audience amateur
python main.py add WelcomeAgain --version 1.0.1 --section "API Methods" --audience amateur
python main.py add Intro --version 1.0.0 --section "Tutorials" --audience amateur
python main.py add Intro --version 1.1.0 --section "Tutorials" --audience amateur
python main.py add Summary --version 1.0.0 --section "Historical Notes" --audience expert
python main.py add Summary --version 1.2.0 --section "Historical Notes" --audience expert
python main.py add Conclusion --version 2.0.0 --section "Tutorials" --audience expert
python main.py add AdvancedTopic --version 2.1.0 --section "Advanced" --audience expert
python main.py add Appendix --version 1.0.0 --section "Appendix" --audience amateur
python main.py add Appendix --version 1.3.0 --section "Appendix" --audience amateur
python main.py add FAQ --version 1.0.0 --section "Appendix" --audience amateur
python main.py add FAQ --version 1.1.0 --section "Appendix" --audience amateur
python main.py add ReleaseNotes --version 3.0.0 --section "Historical Notes" --audience expert
python main.py add Changelog --version 3.1.0 --section "Historical Notes" --audience expert

# List, show, and build examples

`python main.py list Docs`
`python main.py show Docs 1.0.0`
`python main.py show Docs 1.1.0`
`python main.py show Docs 9.0.0`
`python main.py show Docs 2.0.0 --level amateur`
`python main.py show Docs 9.0.0 --level amateur`
`python main.py build Docs 1.0.0 --out Docs_v1.0.0.md`
`python main.py build Docs 1.1.0 --level amateur --out Docs_v1.1.0.md`
`python main.py build Docs 2.0.0 --out Docs_v2.0.0.md`
`python main.py build Docs 3.0.0 --level amateur --out Docs_v3.0.0.md`
