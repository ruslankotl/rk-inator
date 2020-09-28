# -*- coding: utf8 -*-

"""
Euler numerical integrator with GUI support for the systems of 1st order ODEs
"""

import tkinter as tk
import tkinter.ttk
import re
import numpy as np
import matplotlib.pyplot as plt


def counter(t):
    """
    Reads the chemical equation (coefficient+species)

    :return: the species name, its coefficient
    """
    i = 0
    num = ''
    if t[0].isalpha():
        num = 1

    while not t[i].isalpha():
        num += t[i]
        i += 1

    return [t[i:], num]


def reaction_check(reaction_input):
    try:
        overall_format = re.compile(r"[^+=][a-zA-Z0-9+]*=[a-zA-Z0-9+]*[^+=]$", re.I)
        stray_digits = re.compile(r'(\+|=|^)[\d]+(\+|=|$)')
        of = overall_format.match(reaction_input)
        sd = stray_digits.search(reaction_input)
        if of and sd is None:
            return True
        else:
            return False
    except TypeError:
        pass


def num_check(num_input):
    try:
        num = float(num_input)
        if num > 0:
            return True
        else:
            return False
    except ValueError:
        return False


def nonnegative(num_input):
    try:
        num = float(num_input)
        if num >= 0:
            return True
        else:
            return False
    except ValueError:
        return False


def remove_item(tree):
    selected_items = tree.selection()
    for selected_item in selected_items:
        tree.delete(selected_item)


def create_entry_widget(window, x, start_index, lst):
    """

    :param window:
    :param x: list index
    :param start_index: start placing items by .grid() method from this row
    :param lst: list of species
    :return: Label+Entry
    """
    num_valid = (window.register(nonnegative), '%s')

    new_label = tkinter.ttk.Label(window, text=lst[x].capitalize())
    new_label.grid(row=x+start_index, column=0)

    new_entry = tkinter.ttk.Entry(window, validate='none', validatecommand=num_valid)
    new_entry.grid(row=x+start_index, column=1)

    return new_label, new_entry


def validator(window, tree, reaction, rate):
    """
    A function which validates the reaction and rate input and adds it to the list if valid
    Validation takes place while adding to the list: invalid input is not added
    :param window: window in which entry is taking place
    :param tree: since the reaction display is implemented with ttk.Treeview, the function requires the tree
    :param reaction: input which corresponds to reaction
    :param rate: input which corresponds to the reaction rate
    :return:
    """
    if reaction.validate() & rate.validate():
        tree.insert('', 'end', text=reaction.get(), values=rate.get())
        window.destroy()
    elif not reaction.validate() and not rate.validate():
        tk.messagebox.showinfo(message='Invalid reaction formatting\nRate should be a number greater than 0',
                               parent=window)
    elif not reaction.validate() and rate.validate():
        tk.messagebox.showinfo(message='Invalid reaction formatting', parent=window)
    else:
        tk.messagebox.showinfo(message='Rate should be a number greater than 0', parent=window)


class Application(tk.Frame):
    def __init__(self, master=None):
        # initialise the program
        super().__init__(master)
        self.master = master
        self.pack()
        self.main_menu()
        self.reactions = []
        self.concentrations = {}
        self.name = ''

    def main_menu(self):
        # make it the main screen
        welcome = tkinter.ttk.Label(self, text='Welcome to Eulerinator!')
        welcome.grid(row=0, column=0, columnspan=2)

        name_label = tkinter.ttk.Label(self, text='Filename: ')
        name_label.grid(row=1, column=0)
        name_input = tkinter.ttk.Entry(self)
        name_input.grid(row=1, column=1)

        new_reaction = tk.Button(self, text='Add reaction', command=lambda: self.reaction_entry(tree))
        new_reaction.grid(row=2, column=0)
        clear = tk.Button(self, text='Delete reaction', fg='#ff0000', command=lambda: remove_item(tree))
        clear.grid(row=2, column=1)

        tree = tkinter.ttk.Treeview(self, columns='rate')
        tree.heading('rate', text='Rate')
        tree.grid(row=3, column=0, columnspan=2)

        commit = tk.Button(self, text='Set the concentrations',
                           command=lambda: self.concentrations_set(tree, name_input.get()))
        commit.grid(row=4, column=0, columnspan=2)

        terminate = tk.Button(self, text='Quit', command=self.master.destroy)
        terminate.grid(row=5, column=0, columnspan=2)

        self.bind('<Return>', lambda event=None: commit.invoke())

    def reaction_entry(self, tree):
        """
        A window to enter the reaction and its rate
        :param tree: takes a ttk.Treeview object to display the reactions
        :return:
        """
        entry_window = tk.Toplevel(self.master)
        label = tkinter.ttk.Label(entry_window, text='Enter the reaction\n'
                                                     'Separate the species with the "+" sign\n'
                                                     'E.g. 3A+B=Ca+2D\n'
                                                     'NB: use exponent notation for entering rate',
                                  justify='center')
        label.grid(row=0, column=0, columnspan=3)
        reac_valid = (entry_window.register(reaction_check), '%s')
        reaction = tkinter.ttk.Entry(entry_window, validate='none', validatecommand=reac_valid)
        reaction.grid(row=1, column=0)
        num_valid = (entry_window.register(num_check), '%s')
        text_rate = tkinter.ttk.Label(entry_window, text='Rate: ')
        text_rate.grid(row=1, column=1)
        rate = tkinter.ttk.Entry(entry_window, validate='none', validatecommand=num_valid)
        rate.grid(row=1, column=2)
        validate = tk.Button(entry_window, text='Enter',
                             command=lambda: validator(entry_window, tree, reaction, rate))
        validate.grid(row=2, column=0)
        back = tk.Button(entry_window, text='Back', command=entry_window.destroy)
        back.grid(row=2, column=1)
        entry_window.bind('<Return>', lambda event=None: validate.invoke())

    def concentrations_set(self, tree, name):
        self.reactions = []
        self.concentrations = {}
        species = []
        self.name = name

        for child in tree.get_children():
            self.reactions.append(Reaction(tree.item(child)['text'], tree.item(child)['values'][0]))

        for reaction in self.reactions:
            for reactant in reaction.reactants():
                c = counter(reactant)[0].lower()
                species.append(c)
            for product in reaction.products():
                c = counter(product)[0].lower()
                species.append(c)

        # create the window for input, detect the present species(case-insensitive)
        concentration_window = tk.Toplevel(self.master)
        list1 = sorted(set(species))

        label = tkinter.ttk.Label(concentration_window, text='Enter the concentrations')
        label.grid(row=0, column=0)

        concentration_widgets = [create_entry_widget(concentration_window, x, 1, list1) for x in range(len(list1))]

        send_button = tkinter.ttk.Button(concentration_window, text='Confirm', command=lambda:
                                         self.validate_concentrations
                                         (concentration_widgets, list1, concentration_window))
        send_button.grid(row=1+len(list1), column=0, columnspan=2)

    def validate_concentrations(self, conc_list, var_list, window):

        tracker = True

        for value in conc_list:
            tracker = tracker & value[1].validate()

        if tracker:

            for item in zip(conc_list, var_list):
                self.concentrations[item[1]] = float(item[0][1].get())
            window.destroy()
            time_window = tk.Toplevel(self.master)
            num_valid = (time_window.register(num_check), '%s')
            runtime_label = tkinter.ttk.Label(time_window, text='Simulation timespan')
            runtime_label.grid(row=0, column=0)
            runtime_entry = tkinter.ttk.Entry(time_window, validate='none', validatecommand=num_valid)
            runtime_entry.grid(row=0, column=1)
            timestep_label = tkinter.ttk.Label(time_window, text='Simulation timestep')
            timestep_label.grid(row=1, column=0)
            timestep_entry = tkinter.ttk.Entry(time_window, validate='none', validatecommand=num_valid, text='1e-06')
            timestep_entry.grid(row=1, column=1)
            confirm = tkinter.ttk.Button(time_window, text='Start!',
                                         command=lambda: self.init_cell(runtime_entry, timestep_entry))
            confirm.grid(row=2, column=0, columnspan=2)

        else:
            pass

    def init_cell(self, runtime, timestep):
        if runtime.validate() & timestep.validate():
            cell = Cell(self.name, self.reactions, self.concentrations, float(runtime.get()), float(timestep.get()))
            cell.run()
        else:
            pass


class Cell:
    def __init__(self, name, reactions_list, concentration, runtime, timestep):
        self.name = name
        self.reactions = reactions_list
        self.concentrations = concentration
        self.runtime = runtime
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
                in_rate = in_rate * (coef * (conc ** coef))
                out_rate = out_rate * (conc ** coef)

            for product in reaction.products():
                d = counter(product)
                product_list.append([d[0], d[1]])

            for reactant in reactant_list:
                self.delta[reactant] += in_rate

            for product in product_list:
                self.delta[product[0]] += product[1] * out_rate
        return self.delta

    def run(self):
        from time import time
        t = self.runtime
        aux = 0
        keys = []
        for species in self.concentrations:
            keys.append(species)
        with open(self.name + '.dat', 'w') as f:
            t1 = time()
            f.write('# time\t' + '\t'.join([key for key in keys]) + '\n')
            while self.time <= t:
                if aux == 0:
                    f.write(str(self.time) + '\t' + '\t'.join(str(i) for i in self.concentrations.values()) + '\n')
                self.timeprogress()
                aux = (aux + 1) % 1000

        t2 = time()
        print('Done in ' + str(t2 - t1) + ' seconds!')

    def timeprogress(self):
        self.time += self.timestep
        for i, j in zip(self.concentrations, self.grad_calc()):
            self.concentrations[i] = self.concentrations[i] + self.timestep * self.grad_calc()[i]
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
        return self.name.split('=')[0].split('+')

    def products(self):
        return self.name.split('=')[1].split('+')


root = tk.Tk()
root.title('Eulerinator')
app = Application(master=root)

root.mainloop()
