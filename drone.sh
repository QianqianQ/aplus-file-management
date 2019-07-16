docker run -p 7000:7000 \
  --volume=/var/run/docker.sock:/var/run/docker.sock \
  --volume=/var/lib/drone:/data \
  --env=DRONE_GITHUB_SERVER=https://github.com \
  --env=DRONE_GITHUB_CLIENT_ID=9e9d2511dc68df4a902c \
  --env=DRONE_GITHUB_CLIENT_SECRET=19fbfba5546b82daad190e701d3b89409f0ccd4d \
  --env=DRONE_RUNNER_CAPACITY=2 \
  --env=DRONE_SERVER_HOST=https://github.com \
  --env=DRONE_SERVER_PROTO=http \
  --env=DRONE_TLS_AUTOCERT=true \
  --restart=always \
  --detach=true \
  --name=drone \
  drone/drone:1
