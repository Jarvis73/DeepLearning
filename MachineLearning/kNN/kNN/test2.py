# coding: gbk

""" This is a test for recognition of handwritten numbers with kNN  """

import kNN

################################################################################
#                                                                              #
#                                  ��д����ʶ��                                 #
#                                                                              #
################################################################################

# ���Ժ���
#testVector = kNN.img2vector('./data/digits/0_0.txt')
#print(testVector[0,0:31])
#print(testVector[0,32:63])

# ������ + ����
#kNN.handwritingTest()

# png ͼƬ����ʶ��
trainingMat, hwLabels = kNN.handwritingClassTraining()
for i in range(10):
    filepath = kNN.png2vec("./data/digits/MyDigits/%d.png" % i)
    vecUnderTest = kNN.img2vector(filepath)
    res = kNN.classify0(vecUnderTest, trainingMat, hwLabels, 3)
    print("The handwriting number is: %d (%d for real)" % (res, i))

