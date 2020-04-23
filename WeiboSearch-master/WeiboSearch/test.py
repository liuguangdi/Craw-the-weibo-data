# encoding:UTF-8
import queue
import pandas as pd

def test(strTest, emotionNameY1, likeNumY2):
    likeNum = 5
    enmotonsList = sorted(set(strTest.split(',')))[1:]
    for emotionOne in enmotonsList:
        emotionNameY1.append(emotionOne)
        likeNumY2.append(likeNum)
    df1 = pd.DataFrame({'emotion': emotionNameY1, 'like_num': likeNumY2})
    df1['sum'] = df1.groupby(['emotion'])['like_num'].cumsum()
    print(df1)


if __name__ == '__main__':
    A = ",[心],[心],[心],[二哈],[doge],[ok],[doge]"
    B = [10, 5]
    C = []
    D = []
    test(A,C,D)


