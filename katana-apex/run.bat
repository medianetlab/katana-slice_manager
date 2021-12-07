docker build --no-cache -t 5genesis-athens-apex .

docker run -it -p 23324:23324 -p 5000:5000 --name apex-engine --rm  5genesis-athens-apex

pause
