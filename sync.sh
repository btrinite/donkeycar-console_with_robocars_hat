PI_HOSTNAME=yingwa.local

function sync() {
    rsync -avz --exclude db.sqlite3 ~/projects/dc2/ pi@${PI_HOSTNAME}:~/donkeycar-console-v2
    ssh pi@${PI_HOSTNAME} "sudo service gunicorn restart"

}

sync

while inotifywait -r -e modify,create,delete,move ~/projects/dc2/; do
    sync
done
