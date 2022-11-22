#%%
import numpy as np

from _util import (
    physical_constants, set_plot_params, index_finder)
from _util__soen import (
    dend_load_rate_array, dend_load_arrays_thresholds_saturations)
from soen_sim import input_signal, synapse, neuron, network
from soen_sim_lib__common_components__simple_gates import (
    common_dendrite, common_synapse, common_neuron)

from super_input import SuperInput
from params import default_neuron_params, nine_pixel_params
from _plotting__soen import raster_plot


from super_input import SuperInput

'''
Here a class for calling from a 'zoo' of possible neurons is implemented.

Plan:
 - Syntax for custom neuron calls based on dendritic structures and parameters.
 - Library of predefined neurons, both bio-inspired and engineering-specific
 - Should include a testing/plotting paradigm inherent in the class
 - Add more explicit connectivity defintions and corresponding plotting
'''


class NeuralZoo():

    def __init__(self,**entries):
        self.__dict__.update(entries)

        if self.type == '3fractal':
            self.fractal_three()

        if self.type == 'single':
            self.single()

        if self.type == 'custom':
            self.custom()
    
    def single(self):

        self.synapse = common_synapse(1)

        self.dendrite = common_dendrite(1, 'ri', self.beta_di, 
                                          self.tau_di, self.ib)
                                    
        self.dendrite.add_input(self.synapse, connection_strength = self.w_sd)

        self.neuron = common_neuron(1, 'ri', self.beta_ni, self.tau_ni, 
                                      self.ib, self.s_th_factor_n*self.s_max_n, 
                                      self.beta_ref, self.tau_ref, self.ib_ref)

        self.neuron.add_input(self.dendrite, connection_strength = self.w_dn)


    def fractal_three(self):
        H = 3 # depth
        n = [3,3] # fanning at each layer, (length = H-1), from soma to synapses

        fractal_neuron = common_neuron(1, 'ri', self.beta_ni, self.tau_ni, 
                                       self.ib, self.s_th_factor_n*self.s_max_n, 
                                       self.beta_ref, self.tau_ref, self.ib_ref)
        fractal_neuron.name = 'name'
        dendrites = [ [] for _ in range(H-1) ]
        synapses = []

        count=0
        count_syn=0
        last_layer = 1
        # returns dendrites[layer][dendrite] = dendrites[H-1][n_h]
        for h in range(H-1): 
            for d in range(n[h]*last_layer):
                dendrites[h].append(common_dendrite(count, 'ri', self.beta_di, 
                                    self.tau_di, self.ib))

                if h == H-2:
                    synapses.append(common_synapse(d))
                    dendrites[h][d].add_input(synapses[d], 
                                              connection_strength = self.w_sd)
                count+=1
            last_layer = n[h]

        for i,layer in enumerate(dendrites):
            # print("layer:", i)
            for j,d in enumerate(layer):
                # print("  dendrite", j)
                if i < H-2:
                    for g in range(n[1]):
                        d.add_input(dendrites[i+1][j*n[1]+g], 
                                    connection_strength=self.w_dd)
                        # print(j,j*n[1]+g)
                    fractal_neuron.add_input(d, connection_strength=self.w_dn)
        self.dendrites = dendrites
        self.synapses = synapses
        self.fractal_neuron = fractal_neuron


    def custom(self):
        custom_neuron = common_neuron(1, 'ri', self.beta_ni, self.tau_ni, 
                                       self.ib_n, self.s_th_factor_n*self.s_max_n, 
                                       self.beta_ref, self.tau_ref, self.ib_ref)
        custom_neuron.name = 'custom_neuron'
        self.neuron = custom_neuron
        if hasattr(self, 'structure'):
            print("structure")
            arbor = self.structure
        elif hasattr(self, 'weights'):
            print("weights")
            arbor = self.weights

        dendrites = [ [] for _ in range(len(arbor)) ]
        synapses = []

        count=0
        count_syn=0
        last_layer = 1
        den_count = 0
        for i,layer in enumerate(arbor):
            c=0
            for j,dens in enumerate(layer):
                sub = []
                for k,d in enumerate(dens):
                    if self.betas:
                        self.beta_di=(np.pi*2)*10**self.betas[i][j][k]
                    if self.biases:
                        self.ib= self.ib_list_ri[self.biases[i][j][k]]
                    if self.types:
                        type = self.types[i][j][k]
                    else:
                        type = 'ri'
                    sub.append(common_dendrite(f"lay{i}_branch{j}_den{k}", type, 
                                        self.beta_di,self.tau_di, self.ib))
                    den_count+=1
                    c+=1
                dendrites[i].append(sub)
        # for d in dendrites:
        #     print(d)
        for i,l in enumerate(dendrites):
            for j, subgroup in enumerate(l):
                for k,d in enumerate(subgroup):
                    if i==0:
                        # print(i,j,k, " --> soma")
                        custom_neuron.add_input(d, connection_strength=self.weights[i][j][k])
                    else:
                        # print(i,j,k, " --> ", i-1,0,j)
                        # print(np.concatenate(dendrites[i-1])[j])
                        # d.add_input(np.concatenate(dendrites[i-1])[j], connection_strength=weights[i][j][k])
                        np.concatenate(dendrites[i-1])[j].add_input(d, connection_strength=self.weights[i][j][k])
        
        if self.syns:
            self.synapses = [[] for _ in range(len(self.syns))]
            for i,group in enumerate(self.syns):
                for j,s in enumerate(group):
                    self.synapses[i].append(common_synapse(s))
            count=0
            print(len(dendrites[len(dendrites)-1][0]))
            for j, subgroup in enumerate(dendrites[len(dendrites)-1]):
                for k,d in enumerate(subgroup):
                    for s in self.synapses[count]:
                        dendrites[len(dendrites)-1][j][k].add_input(s, connection_strength = self.w_sd)
                    count+=1

        self.dendrites = dendrites

        
        # for i,l in enumerate(dendrites):
        #     for j, subgroup in enumerate(l):
        #         for k,d in enumerate(subgroup):
        #             keys = list(d.dendritic_inputs.keys())
                    # print(i,j,k," - >", d.dendritic_connection_strengths)
                    # for k in keys:
                    #     print(i,j,k," - >", d.dendritic_inputs[k].connection_strengths)

                    
    def plot_structure(self):
        # add connection strengths
        # print(self.dendrites[0][0].dendritic_connection_strengths)
        import matplotlib.pyplot as plt
        layers = [[] for i in range(len(self.dendrites))]
        for i in range(len(layers)):
            for j in range(len(self.dendrites[i])):
                layers[i].append(list(self.dendrites[i][j].dendritic_inputs.keys()))
        print(layers)
        colors = ['r','b','g',]
        Ns = [len(layers[i]) for i in range(len(layers))]
        Ns.reverse()
        Ns.append(1)
        for i,l in enumerate(layers):
            for j,d in enumerate(l):
                if len(d) > 0:
                    for k in layers[i][j]:
                        plt.plot([i+.5, i+1.5], [k-3,j+3], '-k', color=colors[j], linewidth=1)
        for i in range(Ns[-2]):
            plt.plot([len(layers)-.5, len(layers)+.5], [i+len(Ns),len(Ns)+1], '-k', color=colors[i], linewidth=1)
        for i,n in enumerate(Ns):
            if n == np.max(Ns):
                plt.plot(np.ones(n)*i+.5, np.arange(n), 'ok', ms=10)
            else:
                plt.plot(np.ones(n)*i+.5, np.arange(n)+(.5*np.max(Ns)-.5*n), 'ok', ms=10)
        plt.xticks([.5, 1.5,2.5], ['Layer 1', 'layer 2', 'soma'])
        plt.yticks([],[])
        plt.xlim(0,len(layers)+1)
        plt.ylim(-1, max(Ns))
        plt.title('Dendritic Arbor')
        plt.show()





    def get_structure(self):
        '''
        Returns structure of dendritic arbor by recursive search of neuron 
        dictionary tree.
            - Returns list of lists containing names of dendrites
            - List index associated with layer
            - List index within lists associated with branch
        '''
        # for w in weights:
        #     print(w)
        # print("\n")
        # Start with checking dendritic inputs to soma and getting their names
        soma_input = self.neuron.dend__nr_ni.dendritic_inputs
        soma_input_names = list(self.neuron.dend__nr_ni.dendritic_inputs.keys())[1:]

        # initialize arbor list and add soma inputs
        arbor = []
        strengths = []
        arbor.append(soma_input_names)
        strengths.append(list(self.neuron.dend__nr_ni.dendritic_connection_strengths.values())[1:])
        # call recursive function to explore all branches
        def recursive_search(input,names,leaf,arbor,count,strengths):
            '''
            Recursive search returns all inputs (however deep) to designated input
                - Takes inputs (and their names) to a given denrite
                - Iterates over each of those input/name pairs
                - Adds to new lists all of the inputs and names to _those_ dendrites
                - Adds the new name list to the growing arbor
                - So long as names list is not empty, calls itself on new names
                - Once leaf node is reached (no new inputs), returns
            '''
            # print(count)
            if leaf == True:
                names_ = []
                inputs_ = []
                strengths_ = []
                for d in names:
                    names_.append(list(input[d].dendritic_inputs))
                    inputs_.append(input[d].dendritic_inputs)
                    strengths_.append(list(input[d].dendritic_connection_strengths.values()))

                if len(names_) > 0:
                    if len(names_[0]) > 0:
                        arbor.append(names_)
                        strengths.append(strengths_)
                    # print("Leaf reached!")

                for i,input_ in enumerate(inputs_):
                    count+=1
                    # print(count)
                    recursive_search(input_,names_[i],leaf,arbor,count,strengths)
                    
            return arbor,strengths
        count=0
        arbor,strengths = recursive_search(soma_input,soma_input_names,True,arbor,count,strengths)
        
        # for s in strengths:
        #     print(s)
        # print("\n")
        for a in arbor:
            print(a)
        print("\n")
        # return
        def recursive_squish(b,s,a,strengths,i,count,i_count):
            c = a
            s_ = strengths[i]
            # print(i+1,i+len(arbor[i-1]))
            for j in range(i+1,i+len(arbor[i-1])):
                # print(i+1,i+len(arbor[i-1]))
                c += arbor[j]
                s_ += strengths[j]
                count+=1
            i_count+=len(arbor[i-1])
            b.append(c)
            s.append(s_)
            return b,s,a,strengths,i,count,i_count
            # if i+len(arbor[i-1]) == len(arbor):
            #     break

        b = []
        s = []
        count=1
        i_count=0
        for i,a in enumerate(arbor):
            if i < 2:
                b.append(a)
                s.append(strengths[i])
                count+=1
                i_count+=1
            else:
                b,s,a,strengths,i,count,i_count = recursive_squish(b,s,a,strengths,i,count,i_count)
                # print(i_count,count)
            if i_count == len(arbor):
                break


        arbor = b
        strengths = s
        # for a in strengths:
        #     print(a)
        # print("\n")

        # b = [arbor[0],arbor[1],arbor[2]+arbor[3]+arbor[4]]
        # for a in b:
        #     print(a,"\n")
        # if len(self.weights) != len(arbor):
        #     for i,a in enumerate(arbor):
        #         lists =  sum(type(el)== type([]) for el in a)
        #         if lists > 1:
        #             layer = []
        #             s_layer = []
        #             for j in range(lists):
        #                 if len(arbor) >= lists+j:
        #                     if j == 0:
        #                         layer = arbor[lists+j]
        #                         s_layer = strengths[lists+j]
        #                     else:
        #                         layer = layer + arbor[lists+j]
        #                         s_layer = s_layer + strengths[lists+j]
        #             arbor[i+1] = layer
        #             strengths[i+1] = s_layer
        #             for j in range(lists-1):
        #                 del arbor[lists+1+j]
        #                 del strengths[lists+1+j]
        #         if len(arbor)==i+lists:
        #             break
                
        return arbor,strengths





    def plot_custom_structure(self):
        import matplotlib.pyplot as plt
        import matplotlib.colors as mcolors
        colors = mcolors.TABLEAU_COLORS
        c_names = list(colors) + list(colors) + list(colors)
        # print(c_names[0])
        # print(colors[c_names[0]])
        arbor,strengths = self.get_structure()

        # colors = ['r','b','g',]
        Ns = []
        for i,a in enumerate(arbor):
            count = 0
            lsts = sum(type(el)== type([]) for el in a)
            if lsts > 0:
                for j in range(lsts):
                    count+=len(arbor[i][j])
            else: count = len(a)
            Ns.append(count)
        Ns.insert(0,1)
        Ns.reverse()
        arbor[0] = [arbor[0]]
        strengths[0] = [strengths[0]]
        for a in arbor:
            print(a,"\n")
        layers=len(arbor)
        Ns_ = Ns[::-1]
        # Ns_.reverse()
        m=max(Ns)
        # print(Ns_)
        # arbor.reverse()
        c_dexes=[[] for _ in range(len(Ns))]
        for i,l in enumerate(arbor):
            count= 0
            row_sum = 0
            for j,b in enumerate(l):
                for k,d in enumerate(b):
                    if i == 0:
                        c_dexes[i].append(k)
                        if strengths[i][j][k] >= 0:
                            plt.plot([layers-i-.5, layers-i+.5], [(m/2)+(len(b)/2)-(k+1),(m/2)-.5], '-',color=colors[c_names[k]], linewidth=strengths[i][j][k]*5)
                        else:
                            plt.plot([layers-i-.5, layers-i+.5], [(m/2)+(len(b)/2)-(k+1),(m/2)-.5], '--',color=colors[c_names[k]], linewidth=strengths[i][j][k]*5*(-1))
                    else:
                        c_dexes[i].append(c_dexes[i-1][j])
                        c_index = c_dexes[i-1][j]
                        y1=(m/2)+Ns_[i+1]/2 - 1 - (j+k) - row_sum #- ((Ns_[i]/2)%2)/2
                        y2=(m/2)+Ns_[i]/2 - j - 1 
                        # print(i,j,k,row_sum)
                        if strengths[i][j][k] >= 0:
                            plt.plot([layers-i-.5, layers-i+.5], [y1,y2], '-', color=colors[c_names[c_index]], linewidth=strengths[i][j][k]*5)
                        else:
                            plt.plot([layers-i-.5, layers-i+.5], [y1,y2], '--', color=colors[c_names[c_index]], linewidth=strengths[i][j][k]*5*(-1))
                    count+=1
                row_sum += len(arbor[i][j])-1 

        x_ticks=[]
        x_labels=[]
        for i,n in enumerate(Ns):
            x_labels.append(f"L{len(Ns)-(i+1)}")
            x_ticks.append(i+.5)
            if n == np.max(Ns):
                plt.plot(np.ones(n)*i+.5, np.arange(n), 'ok', ms=100/(np.max(Ns)))
            elif n != 1:
                factor = 1 # make proportional
                plt.plot(np.ones(n)*i+.5, np.arange(n)*factor+(.5*np.max(Ns)-.5*n), 'ok', ms=100/(np.max(Ns)))
            else:
                plt.plot(np.ones(n)*i+.5, np.arange(n)+(.5*np.max(Ns)-.5*n), '*k', ms=30)
                plt.plot(np.ones(n)*i+.5, np.arange(n)+(.5*np.max(Ns)-.5*n), '*y', ms=20)
        x_labels[-1]="soma"


        plt.yticks([],[])
        plt.xticks(x_ticks,x_labels)
        plt.xlim(0,len(Ns))
        plt.ylim(-1, max(Ns))
        plt.xlabel("Layers",fontsize=16)
        plt.ylabel("Dendrites",fontsize=16)
        plt.title('Dendritic Arbor',fontsize=20)
        plt.show()


# structure = [
#              [2],
#              [3,2],
#              [3,2,0,2,2]
#             ]

# weights = [
#            [[.2,-.5,.2]],
#            [[.2,.5,-.4],[.2,-.2],[.2,.2]],
#            [[.1,-.1,.1],[-.7,.7],[0],[-.5,.6],[.3,.2],[.1,.3],[.1,.2]],
#            [[.3,.1],[.3,.1],[.3,.1],[.3,.1],[.3,.1],[.3,.1],[.3,.1],
#            [.3,.1],[.3,.1],[.3,.1],[.3,.1],[.3,.1],[.3,.1],[.3,.1]]
#           ]

# weights = [
#            [[1,1,1]],
#            [[1,1],[1],[1,-1]],
#            [[1],[1],[1],[-1,-1],[1,1,1]],
#            [[1],[1,1],[1],[1,1],[1],[1],[1,1],[1,1]]
#           ]

# weights = [
#     [[.3,.3,.3]],
#     [[.3,.3,.3],[.3,.3,.3],[.3,.3,.3]],
#     [[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3]],
#     [[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3]],
#     # [[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3]],
#     # [[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3],[.3,.3,.3]]
#           ]

# weights = [
#     [[.5,.5,.5]],
#     [[0.35,-0.65],[0.35,-0.65],[0.35,-0.65]],
#     [[.6,.5],[.6,.5],[.6,.5],[.6,.5],[.6,.5],[.6,.5]]
# ]

# betas = [
#     [[2,2,2]],
#     [[2,2],[2,2],[2,2]],
#     [[2,2],[2,2],[2,2],[2,2],[2,2],[2,2]]
# ]

# biases = [
#     [[1,1,1]],
#     [[5,5],[5,5],[5,5]],
#     [[-4,3],[-4,3],[-4,3],[-4,3],[-4,3],[-4,3]]
# ]

# for w in weights:
#     print(w)
# arb = NeuralZoo(type="custom",weights=weights,**default_neuron_params) 

# arb = NeuralZoo(type="custom",**nine_pixel_params) 
# arb.get_structure()
# arb.plot_custom_structure()

#%%


# indices = np.array([0,1,3,7,8]) # z-pixel array
# times = np.ones(len(indices))*50
# def_spikes = [indices,times]
# input = SuperInput(channels=9, type='defined', defined_spikes=def_spikes, duration=500)
# print(input.spike_arrays)
# for g in arb.synapses:
#     for s in g:
#         for i,row in enumerate(input.spike_rows):
#             if i == int(s.name)-1:
#                 s.add_input(input_signal(name = 'input_synaptic_drive', input_temporal_form = 'arbitrary_spike_train', spike_times = row))

# net = network(name = 'network_under_test')
# net.add_neuron(arb.neuron)
# net.run_sim(dt = .1, tf = 100)
# net.get_recordings()
# spikes = [net.spikes[0],net.spikes[1]*1000]
# print(spikes)
# raster_plot(spikes,duration=100)




#%%
# raster_plot(input.spike_arrays)


# print(arb.neuron.dend__nr_ni.dendritic_inputs['lay0_branch0_den1'].__dict__)
# print(arb.neuron.__dict__)
# arb = NeuralZoo(type="3fractal",**default_neuron_params) 
# arb.plot_structure()

# neuron_dict = arb.neuron.__dict__
# for k,v in neuron_dict.items():
#     print(k)

# print(arb.neuron.dend__nr_ni.dendritic_inputs)












#%% -----------------------------
# times = np.arange(0,500,50)
# indices = np.zeros(len(times)).astype(int)
# def_spikes = [indices,times]

# # input_ = SuperInput(channels=1, type='random', total_spikes=int(500/42), duration=500)
# input = SuperInput(channels=1, type='defined', defined_spikes=def_spikes, duration=500)

# # print(input.spike_rows)
# # raster_plot(input.spike_arrays)

# default_neuron_params['w_dn'] = 0.42
# default_neuron_params['tau_di'] = 1000
# default_neuron_params['tau_ref'] = 50
# default_neuron_params["s_th_factor_n"] = 0.1

# neo = NeuralZoo(type='single',**default_neuron_params)

# neo.synapse.add_input(input.signals[0])

# net = network(name = 'network_under_test')
# net.add_neuron(neo.neuron)
# # net.neurons['name'].name = 1
# net.run_sim(dt = .1, tf = 500)
# tau_convert = 1/net.neurons[1].time_params['t_tau_conversion']
# net.get_recordings()
# spikes = [net.spikes[0],net.spikes[1]*1000]
# # print(spikes)

# raster_plot(spikes,duration=500)
# spd = neo.dendrite.synaptic_inputs[1].phi_spd
# dend_s = neo.dendrite.s
# signal = net.neurons[1].dend__nr_ni.s
# ref = net.neurons[1].dend__ref.s

# import matplotlib.pyplot as plt
# plt.figure(figsize=(12,4))
# plt.plot(spd[::10], label='phi_spd')
# plt.plot(dend_s[::10], label='dendtrite signal')
# plt.plot(signal[::10], label='soma signal')
# plt.plot(ref[::10], label='refractory signal')
# spike_height = [signal[::10][int(net.spikes[1][x]*1000)] for x in range(len(net.spikes[1]))]
# plt.plot(net.spikes[1]*1000,spike_height,'xk', label='neuron fires')
# plt.legend()



# default_neuron_params['w_dd'] = 1
# default_neuron_params['w_dn'] = 1
# default_neuron_params['tau_di'] = 100


# neo = NeuralZoo(type='3fractal',**default_neuron_params)

# neo.plot_structure()

# print(neo.fractal_neuron.__dict__)
# print

# for k,v in neo.fractal_neuron.__dict__.items():
#     print(k,v)



#%%
# for i in range(len(neo.synapses)):
#     in_ = input_signal(name = 'input_synaptic_drive', 
#                        input_temporal_form = 'arbitrary_spike_train', 
#                        spike_times = input.spike_rows[i])
#     neo.synapses[i].add_input(in_)

# net = network(name = 'network_under_test')
# net.add_neuron(neo.fractal_neuron)
# net.neurons['name'].name = 1
# print(net.neurons['name'].name)
# # network_object.neurons[neuron_key].dend__ref.synaptic_inputs['{}__syn_refraction'.format(network_object.neurons[neuron_key].name)].spike_times_converted = np.append(network_object.neurons[neuron_key].dend__ref.synaptic_inputs['{}__syn_refraction'.format(network_object.neurons[neuron_key].name)].spike_times_converted,tau_vec[ii+1])
# net.run_sim(dt = 10, tf = 1000)


# spikes = [ [] for _ in range(2) ]
# S = []
# Phi_r = []
# count = 0
# for neuron_key in net.neurons:
#     s = net.neurons[neuron_key].dend__nr_ni.s
#     S.append(s)
#     phi_r = net.neurons[neuron_key].dend__nr_ni.phi_r
#     Phi_r.append(phi_r)
#     spike_t = net.neurons[neuron_key].spike_times
#     spikes[0].append(np.ones(len(spike_t))*count)
#     spikes[1].append(spike_t)
#     count+=1
# spikes[0] =np.concatenate(spikes[0])
# spikes[1] = np.concatenate(spikes[1])/1000



# # %%

# %%
