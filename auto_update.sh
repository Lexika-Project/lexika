cd /home/ubuntu/lexika
while [ 1 ]
do
    git fetch > /dev/null
    output_git=$(git status -uno)
    output_ps=$(ps -a)
    if [[ $output_git == *"behind"* || $output_ps != *"python"* ]]
    then 
        screen -X -S server quit
        git reset --hard
        git pull
        cd site
        sudo pip install --ignore-installed -r requirements.txt
        screen -S server -d -m sudo python server.py
        cd ..
    fi
    sleep 5
done

