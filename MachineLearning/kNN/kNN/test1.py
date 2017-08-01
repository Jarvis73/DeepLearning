# coding: gbk

import kNN
import numpy as np


################################################################################
#                                                                              #
#                                    Լ����վ                                   #
#                                                                              #
################################################################################
#group, labels = kNN.createDataSet()
#tlabel = kNN.classify0([0, 0], group, labels, 3)
#print(tlabel)

# ����Լ����������
datingDataMat, datingLabels = kNN.file2matrix('./data/datingTestSet2.txt')

# �� Matplotlib ����ɢ��ͼ
import matplotlib
import matplotlib.pyplot as plt
#fig = plt.figure()
#ax = fig.add_subplot(111)
#ax.scatter(datingDataMat[:,1], 
#           datingDataMat[:,2], 
#           15.0 * np.array(datingLabels), 
#           15.0 * np.array(datingLabels)
#           )
#plt.xlabel('����Ϸ��Ƶ����ʱ��ٷֱ�', fontproperties='SimHei')
#plt.ylabel('ÿ�����ѵı���ܹ�����', fontproperties='SimHei')
#plt.show()

# ��ȡ����
all_cls = np.unique(datingLabels)

fig = plt.figure()
ax = fig.add_subplot(111)

# ��ͼ��ɫ
color = ['Blue', 'Yellow', 'Red']

# ����ͬ�����ͼ
sca = [None] * len(all_cls)
for i, cls in enumerate(all_cls):
    sca[i] = ax.scatter(datingDataMat[datingLabels == cls, 0], 
                        datingDataMat[datingLabels == cls,1], 
                        15.0 * np.array(datingLabels[datingLabels == cls]), 
                        color[i % 3])

plt.xlabel('ÿ���ȡ�ķ��г��������')
plt.ylabel('����Ϸ��Ƶ����ʱ��ٷֱ�')
plt.legend(tuple(sca), ('��ϲ��', '����һ��', '��������'))
plt.savefig('image/fig1.png')

# ��һ��
#normMat, ranges, minVals = autoNorm(datingDataMat)

# ����������
#kNN.datingClassTest()

# Լ����վԤ��
#kNN.classifyPerson()


