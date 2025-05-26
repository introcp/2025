all:
	@echo "Available targets: "

local-action-build:
	./bin/act -j build --cache-server-path=./.artifacts

install-local-act:
	@echo "Install local executor for GitHub Actions"
	curl --proto '=https' --tlsv1.2 -sSf https://raw.githubusercontent.com/nektos/act/master/install.sh | bash

docker-build:
	docker build -t introcp .

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

docker-push:
	docker image tag introcp ercoppa/introcp:latest
	docker push ercoppa/introcp:latest

build-book:
	rm -rf _build/html || echo "nothing to clean"
	. ~/.venv/bin/activate; python scripts/gen-notebook-no-solution.py
	. ~/.venv/bin/activate; jupyter-book build --config _config.jupyterbook.yml .
	# DEBUG="pw:browser"
	. ~/.venv/bin/activate; python3 scripts/convert-all-to-slides.py
	cp -r docs/.hashes . || true
	rm -rf docs ; mkdir docs && cp -r _build/html/* docs && mv .hashes docs || true
	. ~/.venv/bin/activate; python3 scripts/add-slide-button.py docs
	. ~/.venv/bin/activate; python3 scripts/copy-slides-to-book.py docs
	. ~/.venv/bin/activate; python3 scripts/fix-absolute-img-url.py
	rm -rf docs/src/dist; cp -a src/dist docs/src/
	rm -rf docs/dist; cp -a src/dist docs/
	cp -a src/dist/plugin docs/src/
	rm -rf docs/docs

publish:
	git add docs

clean-book:
	rm -rf _build || echo "nothing to clean"