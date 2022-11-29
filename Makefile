build:
	docker build -t gnpsfbmngroups . 

bash:
	docker run -it --rm gnpsfbmngroups /bin/bash

server-compose-build-nocache:
	docker-compose --compatibility build --no-cache

server-compose-interactive:
	docker-compose --compatibility build
	docker-compose --compatibility up

server-compose:
	docker-compose --compatibility build
	docker-compose --compatibility up -d

server-compose-production:
	docker-compose --compatibility build
	docker-compose --compatibility up -d
	
attach:
	docker exec -i -t gnpsfbmngroups-dash /bin/bash
