#!/bin/sh -x
#
T1=9
T2=20

SpeakClient.py 'こんにちは'
sleep $T1
SpeakClient.py '私は二そくほこうロボット'
SpeakClient.py 'オットーパイ と申します'
sleep $T1
SpeakClient.py '障害物を避けながら'
SpeakClient.py '自動で 歩き回ります'
sleep $T1
SpeakClient.py 'ときどき踊ります'
sleep $T1
SpeakClient.py '私はラズベリーパイ ゼロ をベースに'
SpeakClient.py 'サーボモーターと'
SpeakClient.py 'ごく簡単な追加回路だけで作られています'
sleep $T1
SpeakClient.py 'ソフトウエアは'
SpeakClient.py 'パイソン言語で書かれています'
sleep $T1
SpeakClient.py 'よろしくお願いいたします'
sleep $T2
