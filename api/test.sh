#!/bin/bash

echo -e "\n[1] PAP KİMLİK DOĞRULAMASI"

docker exec -it nac-freeradius radtest employee emp123 localhost 0 testing123
sleep 2

echo -e "\n[2] MAB KİMLİK DOĞRULAMASI"

echo "User-Name = AA-BB-CC-DD-EE-FF, User-Password = AA-BB-CC-DD-EE-FF, Calling-Station-Id = AA-BB-CC-DD-EE-FF" \
| docker exec -i nac-freeradius radclient -x 127.0.0.1:1812 auth testing123
sleep 2

echo -e "\n[3] ACCOUNTING START "

echo "User-Name = employee, Acct-Session-Id = EMP-SESSION-001, NAS-IP-Address = 192.168.1.10, Acct-Status-Type = Start" \
| docker exec -i nac-freeradius radclient -x 127.0.0.1:1813 acct testing123



echo -e "\n[4] BRUTE-FORCE RATE LIMITING TESTİ"

for i in {1..6}; do 
  echo "Deneme $i..."
  curl -s -X POST http://localhost:8000/auth -H "Content-Type: application/json" -d '{"username": "hacker", "password": "123"}'
  echo ""
done

sleep 2

echo -e "\n[5] ACCOUNTING STOP"

echo "User-Name = employee, Acct-Session-Id = EMP-SESSION-001, NAS-IP-Address = 192.168.1.10, Acct-Status-Type = Stop" \
| docker exec -i nac-freeradius radclient -x 127.0.0.1:1813 acct testing123
