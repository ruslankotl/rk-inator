# -*- coding: utf8 -*-

"""
Euler numerical integrator with GUI support for the systems of 1st order ODEs
Changed GUI design to Notebook
"""

import tkinter as tk
import tkinter.ttk
import re
import numpy as np
import matplotlib.pyplot as plt

# processes coefficients
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

    return [t[i:], int(num)]


# allows to generate variable number of concentration boxes
def display_concentrations(window, x, start_index, lst):
    """

    :param window:
    :param x: list index
    :param start_index: start placing items by .grid() method from this row
    :param lst: list of species
    :return: Label+Entry
    """
    num_valid = (window.register(nonnegative), '%s')

    new_label = tkinter.ttk.Label(window, text=lst[x].capitalize())
    new_label.grid(row=x + start_index, column=0)

    new_entry = tkinter.ttk.Entry(window, validate='none', validatecommand=num_valid)
    new_entry.grid(row=x + start_index, column=1)

    new_checkbutton = tkinter.ttk.Checkbutton(window, text='Plot')
    new_checkbutton.grid(row=x + start_index, column=2)

    return new_label, new_entry, new_checkbutton

# checks that the string only contains letters, numbers, and an underscore
def name_check(name_input):
    check = re.compile(r'[A-Za-z0-9_]+')
    if check.match(name_input):
        return True
    else:
        return False

# checks that the reaction is entered correctly
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

# checks for positive floats
def num_check(num_input):
    try:
        num = float(num_input)
        if num > 0:
            return True
        else:
            return False
    except ValueError:
        return False


# checks for non-negative numbers (concentrations)
def nonnegative(num_input):
    try:
        num = float(eval(num_input))
        if num >= 0:
            return True
        else:
            return False
    except ValueError:
        return False

# deletes a selected reaction
def remove_item(tree):
    selected_items = tree.selection()
    for selected_item in selected_items:
        tree.delete(selected_item)


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


class Application(tkinter.ttk.Notebook):
    def __init__(self, master=None):
        # initialise the program
        super().__init__(master)
        self.master = master
        self.pack()
        self.main_menu()
        self.reactions = []
        self.concentrations = {}
        self.name = ''
        self.runtime = 0
        self.timestep = 0
        self.skip = 0
        self.time = 0
        self.delta = {}
        self.plotthis = {}


    def main_menu(self):
        set_reactions = tkinter.ttk.Frame(self)  # first page
        set_concentrations = tkinter.ttk.Frame(self)  # second page
        set_simulation = tkinter.ttk.Frame(self) # third page
        self.add(set_reactions, text='Reactions')
        self.add(set_concentrations, text='Concentrations', state='disabled')
        self.add(set_simulation, text='Simulation', state='disabled')

        # save reactions, proceed to concentration input
        def save_reactions():
            if name_input.validate() is False:
                tkinter.messagebox.showinfo(message='Please enter the name', parent=self)
                return
            self.name = name_input.get()
            self.reactions = []
            self.concentrations = {}
            species = []

            if tree.get_children():
                # refresh the concentrations window
                for widget in set_concentrations.winfo_children():
                    widget.destroy()

                # instantiate the reactions present
                for child in tree.get_children():
                    self.reactions.append(Reaction(tree.item(child)['text'], float(tree.item(child)['values'][0])))

                # collect all the species from the reactions
                for reaction in self.reactions:
                    for reactant in reaction.reactants():
                        c = counter(reactant)[0]
                        species.append(c)
                    for product in reaction.products():
                        c = counter(product)[0]
                        species.append(c)
                self.species = sorted(set(species))

                # second screen

                label2 = tkinter.ttk.Label(set_concentrations, text='Enter the concentrations')
                label2.grid(row=0, column=0)

                # see display_concentrations outside the function
                concentration_widgets = [display_concentrations(set_concentrations, x, 1, self.species) for x in
                                         range(len(self.species))]

                # process concentrations
                def validate_concentrations(conc_list, var_list):
                    tracker = True
                    for value in conc_list:
                        try:
                            tracker = tracker & value[1].validate()
                        except tk.TclError:
                            tracker = False
                            break
                    if tracker:
                        for item in zip(conc_list, var_list):
                            self.concentrations[item[1]] = float(item[0][1].get())
                        self.tab(set_simulation, state='normal')
                        self.select(set_simulation)
                    else:
                        tk.messagebox.showinfo(message='Check your concentrations', parent=self)

                send_button = tkinter.ttk.Button(set_concentrations, text='Confirm',
                                                 command=lambda:
                                                 validate_concentrations(concentration_widgets, self.species))
                send_button.grid(row=1 + len(self.species), column=0, columnspan=2)

                # re-enable 'Concentrations' tab
                self.tab(set_concentrations, state='normal')
                self.select(set_concentrations)
            else:
                tk.messagebox.showinfo(message='Consider adding reactions', parent=self)

        # first screen
        welcome = tkinter.ttk.Label(set_reactions, text='Welcome to Eulerinator!')
        welcome.grid(row=0, column=0, columnspan=2)

        name_valid = (set_reactions.register(name_check), '%P')

        name_label = tkinter.ttk.Label(set_reactions, text='Filename: ')
        name_label.grid(row=1, column=0)
        name_input = tkinter.ttk.Entry(set_reactions, validate='key', validatecommand=name_valid)
        name_input.grid(row=1, column=1)

        new_reaction = tk.Button(set_reactions, text='Add reaction', command=lambda: self.reaction_entry(tree))
        new_reaction.grid(row=2, column=0)
        clear = tk.Button(set_reactions, text='Delete reaction', fg='#ff0000', command=lambda: remove_item(tree))
        clear.grid(row=2, column=1)

        tree = tkinter.ttk.Treeview(set_reactions, columns='rate')
        tree.heading('rate', text='Rate')
        tree.grid(row=3, column=0, columnspan=2)

        commit = tk.Button(set_reactions, text='Save reactions & proceed',
                           command=lambda: save_reactions())
        commit.grid(row=4, column=0, columnspan=2)

        terminate = tk.Button(set_reactions, text='Quit', command=self.master.destroy)
        terminate.grid(row=5, column=0, columnspan=2)

        # start up the system

        def simulation():

            self.time = 0
            # self.delta = {}
            self.skip = int(data_entry.get())
            self.timestep = float(timestep_entry.get())
            print(self.concentrations)
            self.run()

            # progress = tk.Toplevel(self)
            # progress_bar = tkinter.ttk.Progressbar(progress, mode='indeterminate')

            tkinter.messagebox.showinfo(message='calculation done', parent=self)

            data = np.loadtxt(self.name+'.dat', unpack=True)

            fig = plt.Figure(figsize=(5, 4), dpi=100)
            ax = fig.add_subplot(111)
            #  line = tk.FigureCanvasTkAgg(fig, self)
            #  line.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH)



            for species in range(data.shape[0]-1):
                plt.plot(data[0], data[species+1])

            ax.set_xlabel('time / s')
            ax.set_ylabel('concentration/M')

            #ax.legend()

            plt.savefig(self.name+'.png')

            plt.show()


        # third screen


        num_valid = (set_simulation.register(num_check), '%s')
        runtime_label = tkinter.ttk.Label(set_simulation, text='Simulation runtime, s')
        runtime_label.grid(row=0, column=0)
        runtime_entry = tkinter.ttk.Entry(set_simulation, validate='focusout', validatecommand=num_valid)
        runtime_entry.grid(row=0, column=1)
        timestep_label = tkinter.ttk.Label(set_simulation, text='Simulation timestep, s')
        timestep_label.grid(row=1, column=0)
        timestep_entry = tkinter.ttk.Combobox(set_simulation, values=(1e-6, 1e-5, 'Custom...'), validate='none', validatecommand=num_valid)
        timestep_entry.grid(row=1, column=1)
        data_label = tkinter.ttk.Label(set_simulation, text='Record every n-th data point')
        data_label.grid(row=2, column=0)
        data_entry = tkinter.ttk.Combobox(set_simulation, values=(1, 10, 100, 1000, 'Custom...'), validate='none', validatecommand=num_valid, state='readonly')
        data_entry.grid(row=2, column=1)

        lf = tkinter.ttk.Labelframe(set_simulation, text='Recording')
        lf.grid(row=3, column=0, columnspan=2)
        test = tkinter.ttk.Label(lf, text='test')
        test.pack()
        confirm = tkinter.ttk.Button(set_simulation, text='Start!',
                                     command=lambda: simulation())
        confirm.grid(row=4, column=0, columnspan=2)

        # updates the label with calculation parameters
        def changer(label):
            if data_entry.get() == 'Custom...':
                new_de = tkinter.ttk.simpledialog.askinteger("Result recording", "Save results in this number of steps",
                                                             parent=set_simulation,
                                                             minvalue=1)
                data_entry.set(new_de)

            if timestep_entry.get() == 'Custom...':
                new_te = tkinter.ttk.simpledialog.askfloat("Timestep", "Set integration step",
                                                           parent=set_simulation,
                                                           minvalue=0)
                timestep_entry.set(new_te)


            try:
                rec_step = float(data_entry.get())*float(timestep_entry.get())
                data_points = float(runtime_entry.get())/rec_step

                label['text'] = 'Will save every {:.2e} s\n{:.0f} datapoints to record'.format(rec_step, data_points)
            except ValueError:
                label['text']='Enter your values'
        data_entry.bind('<<ComboboxSelected>>', lambda event=None: changer(test))
        timestep_entry.bind('<<ComboboxSelected>>', lambda event=None: changer(test))

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
        aux = 0
        keys = []
        for species in self.concentrations:
            keys.append(species)
        with open(self.name + '.dat', 'w') as f:
            t1 = time()
            f.write('# time\t' + '\t'.join([key for key in keys]) + '\n')
            while self.time <= self.runtime:
                if aux == 0:
                    f.write(str(self.time) + '\t' + '\t'.join(str(i) for i in self.concentrations.values()) + '\n')

                self.timeprogress()
                aux = (aux + 1) % self.skip

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
root.title('Eulerinator Mk II')
app = Application(master=root)

root.mainloop()
