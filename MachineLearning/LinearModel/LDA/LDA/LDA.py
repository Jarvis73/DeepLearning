#####################################################
#   coding: gbk
#
#   �����б���� ( Linear Discriminant Analysis )
#
#   ����ѧϰ ��־�� �廪��ѧ������
#
#   ��3�� ����ģ�� ϰ��3.5
#
#   Ŀ��: ʵ�������б����, �������������ݼ� 3.0 alpha �ϵĽ��
#
#   Writen by Jarvis (zjw.math@qq.com)
#
#   Date: 2017.05.03
#

import numpy as np
import matplotlib.pylab as plt


def load_data(file_path, usecols, delim='\t', dtype='float', skiprows=0):
    ''' 
    =================== ��ȡ���� ==================
    ����:
        file_path   �����ļ���·��
        usecols     ��ȡ���к�
        delim       ���ݷָ���, Ĭ��Ϊ '\t'
        dtype       ��������, Ĭ��Ϊ 'float'
        skiprows    ��ͷ����������, Ĭ�ϲ�����
    ���:
        data        ��ȡ����������Ϊ��ά���󷵻�
    ============================================
    '''
    data = np.loadtxt(file_path, delimiter=delim, usecols=usecols, dtype=dtype, skiprows=skiprows)
    return data

def LDA(X1, X2):
    '''
    ================== �����б���� ==================
    ����:
        X1  �������ݼ� ����
        X2  �������ݼ� ����
    ���:
        w   ͶӰֱ�ߵ�ϵ��
    =================================================
    '''
    
    # np.cov��ÿ�е���һ������
    Sw = np.cov(X1.T) * (X1.shape[0] - 1) + np.cov(X2.T) * (X2.shape[0] - 1)
    # �����б�ϵ��
    w = np.dot(np.linalg.inv(Sw), np.mean(X2, axis=0) - np.mean(X1, axis=0))
    return w


def plot_wm(X1, X2, w):
    ''' ������������ɢ��ͼ�Լ�ͶӰֱ�� '''
    plt.scatter(X1[:,0], X1[:,1], s=100, marker=(4, 0), facecolors="B")
    plt.scatter(X2[:,0], X2[:,1], s=100, marker=(3, 0), facecolors="R")
    x = np.linspace(0, 1, 20)
    y = -w[0] * x / w[1]    # w[0]*x + w[1]*y = 0  <==  W^T.X = 0
    plt.plot(x, y)

    plt.xlabel('density')
    plt.ylabel('ratio_sugar')
    plt.title('LDA')
    plt.savefig("LDA.png")
    plt.show()


def main():
    data = load_data('../../wm_data.txt', np.arange(1, 4), skiprows=1)
    X, Y = data[:, 0:2], data[:, 2]
    Y = Y.astype(np.bool)
    X1, X2 = X[Y, :], X[~Y, :]
    w = LDA(X1, X2)

    print("Coefficient: ", w)
    plot_wm(X1, X2, w)


if __name__ == "__main__":
    main()