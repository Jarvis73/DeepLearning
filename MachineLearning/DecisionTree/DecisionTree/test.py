################################################
#   coding: gbk
#
#   ������ ( decision tree ): 
#  
#   ������ѧϰ�� ��־�� �廪��ѧ������ ��4�� ������ 
#
#   1. ������������ 2.0
#   2. ������Ϣ����ͻ���ָ��ѵ��������
#   3. ���ݵõ��ľ��������µ��������Խ���Ԥ��
#   4. �Եõ��ľ��������м�֦����
#
#   Writen by Jarvis (zjw.math@qq.com)
#
#   Date: 2017.05.07
#

from DecisionTree import DecisionTree
import numpy as np


#dt = DecisionTree()
#dt.load_data('wm2.0.csv', np.int)

# 4.2 ����ѡ��
# 4.2.1 ��Ϣ����
#dec_tree = dt.fit(criterion="entropy")
#dt.image(dec_tree, "info_gain")

# 4.2.2 ������

# 4.2.3 ����ָ��
#dec_tree2 = dt.fit(criterion="gini")
#dt.image(dec_tree2, "gini_index")

"""
���Կ���, ����������л���ָ������Ϣ����Ļ��ֽ������ͬ��
"""

# 4.3 ��֦����
# 4.3.1 Ԥ��֦ --> ̫������д��

# 4.3.2 ���֦
#training_data = np.array([0,1,2,5,6,9,13,14,15,16])
#test_data = np.array([3,4,7,8,10,11,12])
#dec_tree3 = dt.fit(training_data, artiSel=True)
#dt.image(dec_tree3, "Nonpruning_tree")
#dec_tree3_pruning = dt.postpruning(dec_tree3, test_data)
#dt.image(dec_tree3_pruning, "Pruning_tree")


# ʹ�� sklearn �⺯�����ɾ�����
#dt2 = DecisionTree()
#dt2.load_data('wm3.0a.csv')

#clf = dt2.train_C45_entropy("entropy")

dt3 = DecisionTree()
dt3.load_data('wm3.0a.csv')

clf = dt3.train_C45_gini("gini")
