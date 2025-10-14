all:
	@echo "Available targets: docker-build, docker-push, docker-run, docker-build-book, build-book, publish, clean-book"

docker-build:
	docker build -t ercoppa/introcp:latest .

docker-push:
	docker push ercoppa/introcp:latest

docker-run:
	docker run --rm -ti \
			-u `id -u`:`id -g` \
			-v $(PWD):/home/user/introcp \
			-w /home/user/introcp \
			--ipc=host --cap-add=SYS_ADMIN --init \
			--name introcp \
			ercoppa/introcp \
			bash

docker-build-book:
	docker run --rm -ti \
			-u `id -u`:`id -g` \
			-v $(PWD):/home/user/introcp \
			-w /home/user/introcp \
			--ipc=host --cap-add=SYS_ADMIN --init \
			--name introcp \
			ercoppa/introcp \
			bash -c "make build-book"

build-book:
	# rm -rf _build/html || echo "nothing to clean"
	# generate website with jupyterbook
	. ~/.venv/bin/activate; jupyter-book build --config _config.jupyterbook.yml .
	# generate slides in HTML and PDF
	. ~/.venv/bin/activate; python3 scripts/convert-notebook-to-PDF-slides.py
	cp -r docs/.hashes . || true
	rm -rf docs ; mkdir docs && cp -r _build/html/* docs && mv .hashes docs || true
	. ~/.venv/bin/activate; python3 scripts/finalize-website.py docs
	rm -rf docs/src/dist; cp -a src/dist docs/src/
	rm -rf docs/dist; cp -a src/dist docs/
	cp -a src/dist/plugin docs/src/
	cp _static/robots.txt docs/
	cp src/download.html docs/src/
	rm -rf docs/docs

publish:
	git add docs

clean-book:
	rm -rf _build || echo "nothing to clean"