################################################
#   coding: gbk
#
#   �������ʻع� ( logistic regression ): 
#  
#   ������ѧϰ�� ��־�� �廪��ѧ������
#
#   ��3�� ����ģ�� ϰ��3.3
#
#   Ŀ��: ʵ�ֶ������ʻع�, �������������ݼ� 3.0 alpha �ϵĽ��
#
#   Writen by Jarvis (zjw.math@qq.com)
#
#   Date: 2017.05.02
#

import numpy as np
import pandas as pd
from scipy.linalg.misc import norm
import matplotlib.pyplot as plt
import mpl_toolkits.mplot3d

import sklearn.linear_model.logistic as logi

def load_data(file_path, **kw):
    ''' 
    =================== ��ȡ���� ==================
    ����:
        file_path   �����ļ���·��
        **kw        һ��������ȡ�������ֵ�
            header      ָ���ļ�����Ϊ�������к�, None��ʾ������
            sep         ���ݷָ���
            encoding    �ļ��ı��뷽ʽ
            index_col   ָ���ļ�����Ϊ��ָ����к�
    ���:
        data        ��ȡ����������Ϊ��ά���󷵻�
    ============================================
    '''
    data = pd.read_table(file_path, **kw)
    X = np.array(data.iloc[:, 0:-1].values[:,:])
    Y = np.array(data.iloc[:, -1].values[:])
    return X, Y


def Newton_iterate(X, Y, B, eps, max_it=10000):
    ''' 
    =================== ţ�ٵ��� ====================
        ����:
            X       ��������, ÿ��һ������
            Y       �������, ����
            B       ��ʼ����ֵ (w; b)
            eps     ����������
            max_it  ����������
        ���:
            B1      �����Ĳ���ֵ (w; b)
            i       ʵ�ʵ�������
    =============================================
    '''

    m = X.shape[0] # number of the samples
    X_hat = np.c_[X, np.ones(m)]

    def p(X, B):
        ''' p(y = 1 | X; B) '''
        tmp = np.exp(np.dot(B, X))
        return tmp / (1 + tmp)
    
    def plpB(X, Y, B):
        ''' l �� B ��һ��ƫ���� '''
        lst = [ X[i,:] * (p(X[i,:].T, B) - Y[i]) for i in range(m) ]
        return np.sum(lst, 0)
        
    def p2lpB2(X, Y, B):
        ''' l �� B �Ķ���ƫ���� '''
        n = X.shape[1]
        _sum = np.zeros((n, n))
        for i in range(m):
            tmp = p(X[i,:], B)
            _sum += np.outer(X[i,:], X[i,:]) * tmp * (1 - tmp)
        return _sum
    
    B1 = B - np.dot(np.linalg.inv(p2lpB2(X_hat, Y, B)), plpB(X_hat, Y, B))

    i = 0
    while norm(B1 - B) > eps:
        B = B1
        B1 = B - np.dot(np.linalg.inv(p2lpB2(X_hat, Y, B)), plpB(X_hat, Y, B))
        i += 1
        if i > max_it:  # ����������
            print("Not converge with ", max_it, "iterations.")
            print("Error norm: ", norm(B1 - B))
            print("(W, b): ", B1)
            exit()
        
    return B1, i


def sigmoid(w, x, b):
    ''' ���ʺ��� '''
    return 1.0 / (1 + np.exp(-np.dot(w, x) - b))


def show_wm(X, Y):
    ''' ������������ '''
    Y = Y.astype(np.bool)
    plt.plot(X[Y,0], X[Y,1], "b*")
    plt.plot(X[~Y, 0], X[~Y, 1], "ro")
    plt.xlim(0, 1)
    plt.ylim(0, 1)
    plt.xlabel('density')
    plt.ylabel('ratio_sugar')
    plt.title("watermelon data")
    plt.savefig('wm_data.png')


def plot_wm(X, Y, B):
    ''' ���ƶ������ʺ���, ����ʾ���ϵ� '''
    x, y = np.ogrid[0:1:50j, 0:1:50j]
    z = 1 / (1 + np.exp(-(B[0] * x + B[1] * y + B[2])))
    
    ''' ���ƶ�������ͼ '''
    fig = plt.figure(figsize=(8, 6))
    ax = plt.subplot(111, projection='3d')
    ax.plot_surface(x, y, z, rstride=2, cstride=1, cmap = plt.cm.Blues_r, alpha = 0.5)
    ax.set_xlabel('density')
    ax.set_ylabel('ratio_sugar')
    ax.set_zlabel('sign')

    ax.scatter(X[:,0], X[:,1], Y, s = 100, marker = "o")
    plt.savefig('logisReg.png')

    
def main():
    X, Y = load_data('../../wm_data.txt', encoding='gbk', index_col=0)
    B0 = np.array([0.5, 0.5, 0])    # B0 = (w; b)
    eps = 1e-6

#    show_wm(X, Y)    # �������� 3.0 ���ӻ�
    B1, i = Newton_iterate(X, Y, B0, eps)   # ţ�ٵ�����������Ȼ�����ļ�ֵ

    print("Parameter: w = ", B1[0:2])
    print("Parameter: b = ", B1[2])
    print("Iteration steps: i = ", i)


#    plot_wm(X, Y, B1)   # ���ƶ��ʺ��������沢������ݵ�

if __name__ == "__main__":
    main()
