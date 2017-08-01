################################################
#   coding: gbk
#
#   ������ ( decision tree ): 
#  
#   ������ѧϰ�� ��־�� �廪��ѧ������ ��4�� ������ 
#
#   Writen by Jarvis (zjw.math@qq.com)
#
#   Date: 2017.05.07
#

import numpy as np
import os
import csv
import json
from graphviz import Digraph
from os.path import join, dirname
from json import dumps
from sklearn import tree

class Bunch(dict):
    """ ���ڱ������ݵ��ֵ� """
    def __init__(self, **kwargs):

        return super().__init__(kwargs)

    def __setattr__(self, key, value):
        self[key] = value

    def __dir__(self):
        return self.keys()

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(key)

def MapInit():
    """ ��ʼ����������ӳ���
    Parameters:
        ��
    Returns:
        map: dict   ���ϵ�����ֵ��������ӳ���ֵ�
    """
    map = {}
    module_path = dirname(__file__)
    with open(join(module_path, 'wm_data', 'map.dat'), encoding='gbk') as f:
        for line in f:
            if line.startswith('*'):    # ������ * ��ͷ
                lst = line.replace('\n', '').replace('*', '').split(' ')
                P_key = lst[0]
                map[P_key] = {  # ����������Ӣ���Լ���ŵĹ���
                    'chs':lst[1], 
                    'num':lst[2]}
                continue
            value, key = tuple(line.replace('\n', '').split(' '))   # ����ֵ
            map[P_key][key] = value
    return map

def load_data(file, type=np.float):
    """ ��������
    Parameters:
        file: str           �ļ���
        type: type          ��������
    Returns:
        Bunch����:
            data: ndarray          ����ֵ
            target: ndarray        ����ֵ
            target_names: ndarray  ���
            feature_names: ndarray ����
    """
    module_path = dirname(__file__)
    with open(join(module_path, 'wm_data', file)) as csv_file:
        data_file = csv.reader(csv_file)

        # ���м�¼��������, ������, �������
        tmp = next(data_file)   
        nSamples = int(tmp[0])
        nFeatures = int(tmp[1])
        target_names = np.array(tmp[2:])

        # �ڶ���Ϊ��������
        tmp = next(data_file)   
        feature_names = np.array(tmp[1:-1])

        data = np.empty((nSamples, nFeatures), dtype=type)
        target = np.empty((nSamples, ), dtype=np.int)

        # ��ȡ���ݱ��浽 data �� target ������
        for i, ir in enumerate(data_file):
            data[i] = np.asarray(ir[1:-1], dtype=type)
            target[i] = np.asarray(ir[-1], dtype=np.int)

    return Bunch(data=data, target=target, 
                target_names=target_names, 
                feature_names=feature_names)


class DecisionTree():
    """ �������� 
    ���������·���:
        load_data               ��������
        ent                     ������Ϣ��
        gain                    ������Ϣ����
        gini                    �������ֵ
        gini_index              �������ָ��
        fit                     ѵ������
        image                   ���ƾ�����
        predict                 ���ݾ�����Ԥ��
        postpruning             ���֦
        train_C45_entropy       ʹ�� sklearn �⺯������Ϊ��׼����
        train_C45_gini          ʹ�� sklearn �⺯���Ի�������Ϊ��׼����
    """

    def __init__(self):
        return

    def load_data(self, file, type=np.float):
        """ ��������
        1. ��ʼ��ӳ��� 
        2. ���ļ��ж�ȡ����
        3. ���������ƺͱ�ż���ӳ���
        """
        self.map = MapInit()
        data = load_data(file, type)
        self.data = data.data
        self.target = data.target
        self.target_names = data.target_names
        self.feature_names = data.feature_names
        self.k_feature = np.empty((self.data.shape[1],), dtype=np.int)
        for i in range(self.data.shape[1]):
            self.k_feature[i] = len(np.unique(self.data[:,i]))
        
        return

    def ent(self, y=None):
        """ ������Ϣ��
                    |y|
        Ent(D) = - \SUM pk log2 pk
                    k=1
        Parameters:
            y: ndarray         �������, Ĭ��Ϊ��������
        Returns:
            info_ent: np.float  ��Ϣ��
        """
        if y is None:
            y = self.target

        _, nDv = np.unique(y, return_counts=True)   # ͳ�Ƹ��������
        pk = nDv / y.shape[0]                       # ��������ռ��
        info_ent = -np.sum(pk[i] * np.log2(pk[i]) for i in range(len(nDv)) if pk[i] != 0)

        return info_ent


    def gain(self, feature, idx=slice(None)):
        """ ������Ϣ����
                                      n  |Dv|
        Gain(D, feature) = Ent(D) - \SUM ---- Ent(Dv)
                                     v=1 |D|
        Paramters:
            feature: int/str        ��������
            idx: ndarray           �������±�, Ĭ��Ϊ��������
        Returns:
            info_gain: double       ��Ϣ���� (infomation gain)
        """
        if isinstance(feature, np.int32) or isinstance(feature, int):
            feature_idx = feature
        else:
            feature_idx = self.map[feature]
        X = self.data[idx, feature_idx]
        y = self.target[idx]
        
        nD = len(y)
        Dv, nDv = np.unique(X, return_counts=True)
        info_gain = self.ent(y) - np.sum(nDv[i] / nD * 
                                      self.ent(y[X == Dv[i]]) 
                                      for i in range(len(nDv)))
        return info_gain


    def gini(self, y=None):
        """ �������ֵ
                   |y|  
        Gini(D) = \SUM \SUM  pk pk'
                   k=1 k'!=k
                       |y|
                = 1 - \SUM pk^2
                       k=1
        Parameters:
            y: ndarray         �������, Ĭ��Ϊ��������
        Returns:
            gini: np.float      ����ֵ
        """
        if y is None:
            y = self.target

        _, nDv = np.unique(y, return_counts=True)   # ͳ�Ƹ��������
        pk = nDv / y.shape[0]                       # ��������ռ��
        gini = 1 - np.sum(pk[i] ** 2 for i in range(len(nDv)))

        return gini


    def gini_index(self, feature, idx=slice(None)):
        """ �������ָ��
                                    n  |Dv|
        Gini_index(D, feature) =  \SUM ---- Gini(Dv)
                                   v=1 |D|
        Paramters:
            feature: int/str        ��������
            idx: ndarray           �������±�, Ĭ��Ϊ��������
        Returns:
            gini_idx: double          ����ָ�� (gini index)
        """
        if isinstance(feature, np.int32) or isinstance(feature, int):
            feature_idx = feature
        else:
            feature_idx = self.map[feature]
        X = self.data[idx, feature_idx]
        y = self.target[idx]

        nD = len(y)
        Dv, nDv = np.unique(X, return_counts=True)
        gini_idx = np.sum(nDv[i] / nD * self.gini(y[X == Dv[i]]) for i in range(len(nDv)))

        return gini_idx


    def __unique__(self, X):
        """ �ж϶�ά���� X ���������Ƿ���ͬ
        Parameters:
            X: ndarray     ��ά����
        Returns:
            True/False
        """
        for i in range(X.shape[1]):
            if len(np.unique(X[:,i])) == 1:
                pass
            else:
                return False
        return True


    def __argmax__(self, array, random=False, artiSel=False, feature=None):
        """ ���ڵõ����Ԫ�ص�ָ��
        Paramters:
            array: ndarray      �����������
            random: bool        ������Ԫ�ز�ֹһ��, �򷵻�ʱ�Ƿ����ѡ��, Ĭ�ϲ����
                                ::�������ҵ��ĵ�һ��ָ��
            artiSel: bool       �Ƿ��˹�ѡ�����ֵ
            feature: ndarray    ʣ�������
        Returns:
            arg: int            ���Ԫ�ص�ָ�� 
        """
        if not artiSel:
            if not random:
                return np.argmax(array)
            else:
                max_value = np.max(array)
                lst = [i for i in range(len(array)) if array[i] == max_value]
                return np.random.choice(lst)
        else:
            max_value = np.max(array)
            lst = [i for i in range(len(array)) if array[i] == max_value]
            idx = input("Please choice a index of the feature: " + 
                        str(self.feature_names[feature[lst]]) + 
                        " from 0 to " + 
                        str(len(lst) - 1) + " :\n")
            return lst[int(idx)]

    def __argmin__(self, array, random=False, artiSel=False, feature=None):
        """ ���ڵõ���СԪ�ص�ָ��
        Paramters:
            array: ndarray      �����������
            random: bool        �����СԪ�ز�ֹһ��, �򷵻�ʱ�Ƿ����ѡ��, Ĭ�ϲ����
                                ::�������ҵ��ĵ�һ��ָ��
            artiSel: bool       �Ƿ��˹�ѡ�����ֵ
            feature: ndarray    ʣ�������
        Returns:
            arg: int            ��СԪ�ص�ָ�� 
        """
        if not artiSel:
            if not random:
                return np.argmin(array)
            else:
                min_value = np.min(array)
                lst = [i for i in range(len(array)) if array[i] == min_value]
                return np.random.choice(lst)
        else:
            min_value = np.min(array)
            lst = [i for i in range(len(array)) if array[i] == min_value]
            idx = input("Please choice a index of the feature: " + 
                        str(self.feature_names[feature[lst]]) + 
                        " from 0 to " + 
                        str(len(lst) - 1) + " :\n")
            return lst[int(idx)]


    def fit(self, idx=None, feature=None, criterion="entropy", random=False, artiSel=False):
        """ ѵ�����ݼ�
            ��ʹ����Ϣ������Ϊ���ϻ��ֵ�׼��
            �㷨: �ο� P74 ͼ 4.2
        Parameters:
            idx: ndarray        ��ѵ�����ݵ��±�, Ĭ��Ϊ��������
            feature: ndarray    ���ڷ��������, Ĭ��Ϊ��������
            criterion: str      �����׼, Ĭ��Ϊ "��" , ��ѡ "gini"
            random: bool        ����ָ�����ʱ�Ƿ����ѡ��, Ĭ�ϲ����, ѡ���һ��
            artiSel: bool       ( Artificial select ) ѡ�����Ż�������ʱ, �������ָ�����, �Ƿ��˹�ѡ��, Ĭ���� random ����
                                ::�����ѡ����Ϊ�����ɺ�����һ�µľ�����, ���ڼ���ѧϰ
        Returns:
            tree: Bunch         ������
        

        Example of tree:
            {"Texture": {'samples': [ 0,  1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11, 12, 13, 14, 15, 16]
                         1: {"Root": {'samples': [ 0,  1,  2,  3,  4,  5,  7,  9, 14]
                                      1:  "Good",
                                      2: {"Color": {'samples': [ 5,  7, 14]
                                                    1:  "Good",
                                                    2: {"Touch": {'samples': [ 7, 14]
                                                                  1: "Good",
                                                                  2: "Bad"
                                                                 }
                                                       },
                                                    3:  "Good"
                                                   }
                                         },
                                       3:  "Bad"
                                      }
                             },
                         2: {"Touch": {'samples': [ 6,  8, 12, 13, 16]
                                       1:  "Bad",
                                       2:  "Good"
                                      }
                            },
                         3:  "Bad"
                        }
            }
        """

        # ����Ԥ����
        if feature is None:
            feature = np.array(range(self.data.shape[1]), np.int)
        if idx is None:
            idx = np.array(range(self.data.shape[0]), np.int)

        X = self.data[idx,:][:,feature]
        y = self.target[idx]
        cla, num = np.unique(y, return_counts=True)

        # ����һ�ÿ���
        tree = Bunch()

        # �������ȫ����ͬһ���
        # �� node ���Ϊ����Ҷ�ڵ� ����
        if len(cla) == 1:
            return self.target_names[y[0]]

        # ��� feature Ϊ�� or ���������Լ��ϵ�ȡֵ��ͬ
        # �� node ���ΪҶ�ڵ�, �����Ϊ������������������ ����
        if X.shape[1] == 0 or self.__unique__(X):
            return self.target_names[int(cla[num == np.max(num)][-1])]

        # ѡ�����Ż�������
        if criterion == "entropy":
            info_gain = np.empty((X.shape[1],), np.float)
            for i in range(X.shape[1]):
                info_gain[i] = self.gain(feature[i], idx)
            if not artiSel: # ���˹�ѡ��
                opt_feature = self.__argmax__(info_gain, random=random, artiSel=False)
            else:           # �˹�ѡ��
                opt_feature = self.__argmax__(info_gain, artiSel=True, feature=feature)
        elif criterion == "gini":
            gini_idx = np.empty((X.shape[1],), np.float)
            for i in range(X.shape[1]):
                gini_idx[i] = self.gini_index(feature[i], idx)
            if not artiSel: # ���˹�ѡ��
                opt_feature = self.__argmin__(gini_idx, random=random, artiSel=False)
            else:           # �˹�ѡ��
                opt_feature = self.__argmin__(gini_idx, artiSel=True, feature=feature)
        else:
            raise ValueError("Unknown value \"" + criterion + "\"", "in DecisionTree.py")

        opt_feature_in_all = feature[opt_feature]


        fname = self.feature_names[opt_feature_in_all]
        tree[fname] = {'samples': idx}

        # ���������Ի��������Ӽ�
        for i in range(self.k_feature[opt_feature_in_all]):
            lst_samples = idx[X[:,opt_feature] == i + 1]
            lst_feature = feature[feature != opt_feature_in_all]
            if lst_samples.shape[0] == 0:
                tree[fname][i+1] = self.target_names[int(cla[num == np.max(num)][-1])]
            else:
                tree[fname][i+1] = self.fit(lst_samples, lst_feature)

        return tree


    def __image_link__(self, dot, name, parent_name, parent, children):
        """ �ݹ麯��: 
            �������� Graphviz ͼ�ĸ��׺Ͷ��ӽ��
        Parameters:
            dot: Digraph        ����ͼ����
            name: int           �����, ����ͳһ�����ֱ�ʾ(��Ϊ��ͼ����ʾ���ǽ��� label ���ǽ����
                                    ����ֱ�������ֱ�ʾ��������, Ҳ����ݹ�)
            parent_name: str    �������
            parent: str         ������ label
            children: dict      �ӽ�㼯
        Returns:
            name: int           ��ǰ��ĺ�����������һ�������
        """
        for key in children:                        # key �����Ӹ��׺Ͷ��ӵı� label
            if key == 'samples':
                continue
            if isinstance(children[key], str):      # Ҷ�ӽ��
                dot.node(str(name), self.map[children[key]]['chs'], fontname="SimSun")
                dot.edge(parent_name, str(name), self.map[parent][str(key)], fontname="STKaiti")
                name += 1
                continue
            for subkey in children[key]:            # ��Ҷ�ӽ��, ����ʵ����ֻ��һ���ֵ
                dot.node(str(name), self.map[subkey]['chs'], shape='box', fontname="SimSun")
                dot.edge(parent_name, str(name), self.map[parent][str(key)], fontname="STKaiti")
                name = self.__image_link__(dot, name+1, str(name), subkey, children[key][subkey])
        
        return name


    def image(self, tree, title, format='png'):
        """ Graphviz ��ͼ����
        Parameters:
            tree: Bunch     ��Ҫ���Ƶ��ֵ���
            title: str      ����, ͬʱ��Ϊ������ļ���
            format: str     ����ļ��ĸ�ʽ, Ĭ��Ϊ 'png'
        Returns:
            ��ͼ������� 'image\' �ļ���
                filename.gv         ʹ�� dot ���Ե� Graphviz ͼ�������ļ�
                filename.gv.png     ���Ƴ��ļ�ͷͼ
            ע��: ��������������ʹ�� dot -Tpng -O filename.gv ������ͼ�������ļ������� png ͼ
                 ���õ������ʽ�� -Tpdf -Tpng ��
        """
        dot = Digraph(comment=title, format=format)
        name = 0
        if isinstance(tree, str):       # ֻ��һ�����ڵ�
            dot.node(str(name), self.map[tree]['chs'], fontname="SimSun")
        else:                           # ���ڵ��Ҷ��
            for key in tree:
                dot.node(str(name), self.map[key]['chs'], shape='box', fontname="SimSun")
                self.__image_link__(dot, name+1, str(name), key, tree[key])

        dot.render("image\\" + title + ".gv", view=True)

        return


    def predict(self, tree, idx):
        """ ���þ�����Ԥ��
        Paramters:
            tree: Bunch         ������
            idx: ndarray        ���Լ�ָ��
        Returns:
            _Y: ndarray/int     Ԥ����
        """
        if isinstance(idx, np.ndarray):
            test_set = self.data[idx,:]
        elif isinstance(idx, int):
            test_set = self.data[[idx],:]
        else:
            raise ValueError("Test set should be one or two dimention array")

        res_set = []
        for x in test_set:
            ptr = tree
            while True:
                if isinstance(ptr, str):    # ������Ҷ�ӽ��
                    res_set.append(ptr)
                    break
                else:   # �������Խ����ж�
                    for key in ptr: # ����һ����ֵ��: һ����������
                        fvalue = x[int(self.map[key]['num'])]
                    ptr = ptr[key][fvalue]

        return res_set if len(res_set) > 1 else res_set[0]


    def __postpruning__(self, tree, parent, pkey, idx, root):
        """ ���֦�ݹ麯��
        Paramters:
            tree: Bunch         ������
            parent: Bunch       �����
            pkey: int           tree �ڸ�����µ� key
            idx: ndarray        ���Լ�ָ��
        Returns:
            tree: Bunch         ��֦�����
        """
        if isinstance(tree, str):   # ������ͷ
            return tree             # tree��Ҷ�ӽ��(����), ���ܼ�֦, ֱ�ӷ���
        for key in tree:            # key�Ƿ�Ҷ�ӽ��(����)
            if True in [isinstance(tree[key][subkey], dict) for subkey in tree[key]]:   # key������Ͳ�����, ��Ҫ��������
                for subkey in tree[key]:
                    if subkey == 'samples':
                        continue
                    tree[key][subkey] = self.__postpruning__(tree[key][subkey], tree[key], subkey, idx, root)
            else:   # key����Ͳ������, ���Լ�֦
                # �����֦ǰ�ľ���
                predict_value = np.array([True if cls == 'Good' else False for cls in self.predict(root, idx)])
                real_value = np.array(self.target[idx], dtype=np.bool)
                tmp = predict_value ^ real_value    # ��ͬΪFalse, ��ͬΪTrue
                pre_accur = 1.0 * tmp[tmp == False].shape[0] / tmp.shape[0]
                
                # ���ݷ�֧����֦
                bak_tree = tree.copy()
                cla, num = np.unique(self.target[tree[key]['samples']], return_counts=True)
                parent[pkey] = self.target_names[int(cla[num == np.max(num)][-1])]

                # �����֦��ľ���
                predict_value = np.array([True if cls == 'Good' else False for cls in self.predict(root, idx)])
                real_value = np.array(self.target[idx], dtype=np.bool)
                tmp = predict_value ^ real_value    # ��ͬΪFalse, ��ͬΪTrue
                post_accur = 1.0 * tmp[tmp == False].shape[0] / tmp.shape[0]

                if pre_accur > post_accur:  # �����֦ǰ���ȸ�, ������֦
                    parent[pkey] = bak_tree
                else:                       # �����֦�󾫶ȸ�, ��ȷ�ϼ�֦
                    pass
        return parent[pkey]

    def postpruning(self, tree, idx):
        """ ���֦�ӿ�
        �������к������
        Paramters:
            tree: Bunch         ������
            idx: ndarray        ���Լ�ָ��
        Returns:
            tree: Bunch         ��֦�����
        """
        Dumyhead = {'dumykey': tree}
        
        # �����֦ǰ�ľ���
        predict_value = np.array([True if cls == 'Good' else False for cls in self.predict(tree, idx)])
        real_value = np.array(self.target[idx], dtype=np.bool)
        tmp = predict_value ^ real_value    # ��ͬΪFalse, ��ͬΪTrue
        pre_accur = 1.0 * tmp[tmp == False].shape[0] / tmp.shape[0]

        print("Accuracy before postpruning: %.2f%%" % (pre_accur * 100))
        new_tree = self.__postpruning__(tree, Dumyhead, 'dumykey', idx, tree)
        
        # �����֦�󾫶�
        predict_value = np.array([True if cls == 'Good' else False for cls in self.predict(tree, idx)])
        real_value = np.array(self.target[idx], dtype=np.bool)
        tmp = predict_value ^ real_value    # ��ͬΪFalse, ��ͬΪTrue
        post_accur = 1.0 * tmp[tmp == False].shape[0] / tmp.shape[0]

        print("Accuracy after postpruning:  %.2f%%" % (post_accur * 100))

        return new_tree

    def train_C45_entropy(self, title):
        """ sklearn ���е� C4.5 �㷨 
            ʹ�� "entropy" ��Ϊ���ϻ��ֵ�����
        """
        clf = tree.DecisionTreeClassifier(criterion='entropy')
        clf = clf.fit(self.data, self.target)
        with open("image\\" + title + ".gv", "w") as f:
            f = tree.export_graphviz(clf, out_file=f, 
                                     feature_names=self.feature_names, 
                                     class_names=self.target_names, 
                                     filled=True, rounded=True,
                                     special_characters=True)
        os.system("dot -Tpng -O image\\" + title + ".gv")
        os.system("start image\\" + title + ".gv.png")

        return clf


    def train_C45_gini(self, title):
        """ sklearn ���е� C4.5 �㷨 
            ʹ�� "gini" ��Ϊ���ϻ��ֵ�����
        """
        clf = tree.DecisionTreeClassifier()
        clf = clf.fit(self.data, self.target)
        with open("image\\" + title + ".gv", "w") as f:
            f = tree.export_graphviz(clf, out_file=f, 
                                     feature_names=self.feature_names, 
                                     class_names=self.target_names, 
                                     filled=True, rounded=True,
                                     special_characters=True)
        os.system("dot -Tpng -O image\\" + title + ".gv")
        os.system("start image\\" + title + ".gv.png")

        return clf

