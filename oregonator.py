# -*- coding: utf-8 -*-
"""
Created on Sun Jul 19 15:09:44 2020

@author: Руслан Алексеевич
"""

import numpy as np
import matplotlib.pyplot as plt


def counter(t):
    i = 0
    num = ''
    if t.isalpha():
        num = 1
   
    while not t[i].isalpha():
        num += t[i]
        i += 1
    
    return [t[i:], int(num)]


class Cell:
    def __init__(self, name, reactions_list, concentration, timestep):
        self.name = name
        self.reactions = reactions_list
        self.concentrations = concentration
        self.time = 0
        self.timestep = timestep
        self.delta = {}

    def grad_calc(self):
        for item in self.concentrations:
            self.delta[item] = 0

        for reaction in self.reactions:
            in_rate = -reaction.k
            out_rate = reaction.k
            reactant_list = []
            product_list = []
            
            for reactant in reaction.reactants():
                
                c = counter(reactant)
                reactant_list.append(c[0])
                conc, coef = self.concentrations[c[0]], c[1]
                in_rate = in_rate*(coef*(conc**coef))
                out_rate = out_rate*(conc**coef)

            for product in reaction.products():
                
                d = counter(product)
                product_list.append([d[0], d[1]])

            for reactant in reactant_list:
                self.delta[reactant] += in_rate

            for product in product_list:
                self.delta[product[0]] += product[1]*out_rate
        return self.delta

    def run(self):
        from time import time
        t = float(input('Reaction time, seconds: '))
        aux = 0
        keys = []
        for species in self.concentrations:
            keys.append(species)
        with open(self.name+'.dat', 'w') as f:
            t1 = time()
            f.write('# time\t'+'\t'.join([key for key in keys])+'\n')
            while self.time <= t:
                if aux == 0:
                    f.write(str(self.time)+'\t'+'\t'.join(str(i) for i in self.concentrations.values())+'\n')
                self.timeprogress()
                aux = (aux+1) % 1000
                
        t2 = time()
        print('Done in '+str(t2-t1)+' seconds!')    
     
    def timeprogress(self):
        self.time += self.timestep
        for i, j in zip(self.concentrations, self.grad_calc()):
            self.concentrations[i] = self.concentrations[i]+self.timestep*self.grad_calc()[i]
        return self.concentrations

 
class Reaction:
    def __init__(self, name, k):
        self.name = name
        self.k = k
        
    def name(self):
        return self.name
    
    def k(self):
        return self.k
        
    def reactants(self):
        return self.name.split('->')[0].split('+')
    
    def products(self):
        return self.name.split('->')[1].split('+')
    

reactions = [Reaction('A+Y->X+P', 1.34),
             Reaction('X+Y->P', 1.6e09),
             Reaction('B+X->2X+Z', 8e03),
             Reaction('2X->Q', 4e07),
             Reaction('Z->Y', 1)]

    
concentrations = {'A': 0.06,
                  'B': 0.06,
                  'P': 0,
                  'Q': 0,
                  'X': 10**(-9.8), 
                  'Y': 10**(-6.52),
                  'Z': 10**(-7.32)}

cell = Cell('oregonator3', reactions, concentrations, 1e-6)

cell.run()

'''reactions_test=[Reaction('A->B',1)]  
concentrations_test={'A':1, 'B':0} 
test=Cell('test',reactions_test, concentrations_test, 1e-06)

test.run()'''

'''reactions2=[Reaction('A->B', 10),
            Reaction('B->C', 1)]

concentrations2={'A':1,
                 'B':0,
                 'C':0}

tworeactions = Cell('AtoBtoC', reactions2,concentrations2, 1e-06)

tworeactions.run()'''

data = np.loadtxt('oregonator3.dat', unpack=True)


time, a, b, p, q, x, y, z = data

fig, ax = plt.subplots()

plt.plot(time, x, label='X')
plt.plot(time, y, label='Y')
plt.plot(time, z, label='Z')
plt.yscale('log')

ax.set_xlabel('time / s')
ax.set_ylabel('concentration/M')

ax.legend()

plt.savefig('oregonator3.png')

plt.show()
