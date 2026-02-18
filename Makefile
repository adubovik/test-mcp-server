PORT ?= 5006

docker_serve:
	docker build -f Dockerfile -t mcp/time .
	docker run --env-file ./.env -p $(PORT):5000 mcp/time
