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


def display_concentrations(window, x, start_index, lst, boo):
    """

    :param window:
    :param x: list index
    :param start_index: start placing items by .grid() method from this row
    :param lst: list of species
    :param boo: flag for plotting
    :return: Label+Entry
    """
    num_valid = (window.register(nonnegative), '%s')

    new_label = tkinter.ttk.Label(window, text=lst[x].capitalize())
    new_label.grid(row=x + start_index, column=0)

    new_entry = tkinter.ttk.Entry(window, validate='none', validatecommand=num_valid)
    new_entry.grid(row=x + start_index, column=1)

    new_checkbutton = tkinter.ttk.Checkbutton(window, text='Plot', variable=boo[x])
    new_checkbutton.grid(row=x + start_index, column=2)

    return new_label, new_entry, new_checkbutton, boo[x], x+1


def name_check(name_input):
    check = re.compile(r'[A-Za-z0-9_]+')
    if check.match(name_input):
        return True
    else:
        return False


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
        num = float(eval(num_input))
        if num >= 0:
            return True
        else:
            return False
    except (ValueError, SyntaxError, NameError):
        return False


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
        self.species = []
        self.plot_tuple = (0,)

    def main_menu(self):
        set_reactions = tkinter.ttk.Frame(self)  # first page
        set_concentrations = tkinter.ttk.Frame(self)  # second page
        set_simulation = tkinter.ttk.Frame(self)
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
                boo = [x*0 for x in range(len(self.species))]

                for el in range(len(self.species)):
                    boo[el] = tk.IntVar()

                concentration_widgets = [display_concentrations(set_concentrations, x, 1, self.species, boo) for x in
                                         range(len(self.species))]

                # process concentrations
                def validate_concentrations(conc_list, var_list):
                    tracker = True
                    for value in conc_list:
                        try:
                            tracker = tracker & value[1].validate()
                        except (tk.TclError, NameError, SyntaxError):
                            tracker = False
                            break
                    if tracker:
                        self.plot_tuple = (0,)
                        for item in zip(conc_list, var_list):
                            self.concentrations[item[1]] = float(item[0][1].get())
                            if item[0][3].get() == 1:
                                self.plot_tuple += (item[0][4],)

                        self.tab(set_simulation, state='normal')
                        self.select(set_simulation)
                    else:
                        tk.messagebox.showinfo(message='Check your concentrations', parent=self)

                send_button = tkinter.ttk.Button(set_concentrations, text='Confirm',
                                                 command=lambda:
                                                 validate_concentrations(concentration_widgets, self.species))
                send_button.grid(row=1 + len(species), column=0, columnspan=2)

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

        # start up the system, let the Cell handle maths

        def simulation():
            if method.get() == '':
                tk.messagebox.showinfo(message='Choose the integration method', parent=self)
                return
            cell = Cell(self.name, self.reactions, self.concentrations,
                        float(runtime_entry.get()), float(timestep_entry.get()),
                        int(data_entry.get()), method)
            cell.run()
            # progress = tk.Toplevel(self)
            # progress_bar = tkinter.ttk.Progressbar(progress, mode='indeterminate')

            tkinter.messagebox.showinfo(message='calculation done\n'
                                                ' data saved as '+self.name+'.dat\n'
                                                'Plotting...', parent=self)

            data = np.loadtxt(self.name + '.dat', unpack=True, usecols=self.plot_tuple)
            fig, ax = plt.subplots()

            for sp in range(data.shape[0]-1):
                ind = self.plot_tuple[sp+1]
                plt.plot(data[0], data[sp+1], label=self.species[ind-1])

            ax.set_xlabel('time / s')
            ax.set_ylabel('concentration / M')

            ax.legend()

            plt.savefig(self.name + '.png')

            plt.show()

        # third screen
        num_valid = (set_simulation.register(num_check), '%s')
        runtime_label = tkinter.ttk.Label(set_simulation, text='Simulation runtime, s')
        runtime_label.grid(row=0, column=0)
        runtime_entry = tkinter.ttk.Entry(set_simulation, validate='focusout', validatecommand=num_valid)
        runtime_entry.grid(row=0, column=1)
        timestep_label = tkinter.ttk.Label(set_simulation, text='Simulation timestep, s')
        timestep_label.grid(row=1, column=0)
        timestep_entry = tkinter.ttk.Combobox(set_simulation, values=(1e-6, 1e-5, 'Custom...'),
                                              validate='none', validatecommand=num_valid)
        timestep_entry.grid(row=1, column=1)
        data_label = tkinter.ttk.Label(set_simulation, text='Record every n-th data point')
        data_label.grid(row=2, column=0)
        data_entry = tkinter.ttk.Combobox(set_simulation, values=(1, 10, 100, 1000, 'Custom...'),
                                          validate='none', validatecommand=num_valid, state='readonly')
        data_entry.grid(row=2, column=1)

        lf = tkinter.ttk.Labelframe(set_simulation, text='Recording')
        lf.grid(row=3, column=0, columnspan=2)
        test = tkinter.ttk.Label(lf, text='Please specify simulation parameters')
        test.pack()

        integration = tkinter.ttk.LabelFrame(set_simulation, text='Integration method')
        integration.grid(row=4, column=0, columnspan=2)

        method = tk.StringVar()

        rb_euler = tkinter.ttk.Radiobutton(integration, text='Euler', variable=method, value='euler')
        rb_euler.grid(row=0, column=0)
        rb_heun = tkinter.ttk.Radiobutton(integration, text='Heun', variable=method, value='heun')
        rb_heun.grid(row=0, column=1)
        rb_rk4 = tkinter.ttk.Radiobutton(integration, text='Runge-Kutta', variable=method, value='rk4')
        rb_rk4.grid(row=0, column=2)

        confirm = tkinter.ttk.Button(set_simulation, text='Start!',
                                     command=lambda: simulation())
        confirm.grid(row=5, column=0, columnspan=2)

        # updates the label with calculation parameters
        def changer(label):
            if data_entry.get() == 'Custom...':
                new_de = tkinter.simpledialog.askinteger("Result recording", "Save results in this number of steps",
                                                        parent=set_simulation,
                                                        minvalue=1)
                data_entry.set(new_de)

            if timestep_entry.get() == 'Custom...':
                new_te = tkinter.simpledialog.askfloat("Timestep", "Set integration step",
                                                        parent=set_simulation,
                                                        minvalue=0)
                timestep_entry.set(new_te)

            try:
                rec_step = float(data_entry.get())*float(timestep_entry.get())
                data_points = float(runtime_entry.get())/rec_step

                label['text'] = 'Will save every {:.2e} s\n{:.0f} datapoints to record'.format(rec_step, data_points)
            except ValueError:
                label['text'] = 'Enter your values'
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


# where the reaction runs, handles concentration changes with time
class Cell:
    def __init__(self, name, reactions_list, concentration, runtime, timestep, skip, method):
        self.name = name
        self.reactions = reactions_list
        self.concentrations = concentration
        self.runtime = runtime
        self.time = 0
        self.timestep = timestep
        self.skip = skip
        # delta = {}
        self.method = method.get()

    def grad_calc(self, concentrations_dict):  # calculates gradient, equivalent to k1 in Runge-Kutta
        delta = {}
        for item in concentrations_dict:
            delta[item] = 0

        for reaction in self.reactions:
            in_rate = -reaction.k
            out_rate = reaction.k
            reactant_list = []
            product_list = []

            for reactant in reaction.reactants():
                c = counter(reactant)
                reactant_list.append(c[0])
                conc, coef = concentrations_dict[c[0]], c[1]
                in_rate = in_rate * (coef * (conc ** coef))
                out_rate = out_rate * (conc ** coef)

            for product in reaction.products():
                d = counter(product)
                product_list.append([d[0], d[1]])

            for reactant in reactant_list:
                delta[reactant] += in_rate

            for product in product_list:
                delta[product[0]] += product[1] * out_rate
        return delta

    def heun(self):  # Heun method (will allow for better convergence)
        predicted_concentrations = {}
        gradient1 = self.grad_calc(self.concentrations)  # gradient at t_n
        for i, j in zip(self.concentrations, gradient1):
            predicted_concentrations[i] = self.concentrations[i] + self.timestep * gradient1[i]
        gradient2 = self.grad_calc(predicted_concentrations)  # gradient as extrapolated to t_(n+1)
        for i, j, k in zip(self.concentrations, gradient1, gradient2):
            self.concentrations[i] = self.concentrations[i] + \
                                     self.timestep / 2 * \
                                     (gradient1[i] + gradient2[i])
        self.time += self.timestep
        return self.concentrations

    def runge_kutta4(self):
        k1 = self.grad_calc(self.concentrations)
        increment = {}
        pred1 = {}
        for i, j in zip(self.concentrations, k1):
            pred1[i] = self.concentrations[i] + self.timestep * k1[i] / 2
            increment[i] = k1[i]
        k2 = self.grad_calc(pred1)
        pred2 = {}
        for i, j in zip(self.concentrations, k2):
            pred2[i] = self.concentrations[i] + self.timestep * k2[i] / 2
            increment[i] += 2*k2[i]
        k3 = self.grad_calc(pred2)
        pred3 = {}
        for i, j in zip(self.concentrations, k3):
            pred3[i] = self.concentrations[i] + self.timestep * k3[i]
            increment[i] += 2*k3[i]
        k4 = self.grad_calc(pred3)
        for i, j in zip(self.concentrations, k4):
            increment[i] += k4[i]
            self.concentrations[i] += self.timestep * increment[i] / 6
        self.time += self.timestep
        return self.concentrations

    def run(self):  # generates output
        from time import time
        t = self.runtime
        aux = 0
        keys = []
        integrator = self.method_setup()
        for species in self.concentrations:
            keys.append(species)
        with open(self.name + '.dat', 'w') as f:
            t1 = time()
            f.write('# time\t' + '\t'.join([key for key in keys]) + '\n')
            while self.time <= t:
                if aux == 0:
                    f.write(str(self.time) + '\t' + '\t'.join(str(i) for i in self.concentrations.values()) + '\n')

                integrator()
                aux = (aux + 1) % self.skip

        t2 = time()
        print('Done in ' + str(t2 - t1) + ' seconds!')

    def euler(self):  # time evolution
        for i, j in zip(self.concentrations, self.grad_calc(self.concentrations)):
            self.concentrations[i] = self.concentrations[i] + self.timestep * self.grad_calc(self.concentrations)[i]
        self.time += self.timestep
        return self.concentrations

    def method_setup(self):
        if self.method == 'euler':
            self.method = self.euler
        elif self.method == 'heun':
            self.method = self.heun
        elif self.method == 'rk4':
            self.method = self.runge_kutta4
        return self.method


# instantiates reactions
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

    def reactant_list(self):
        return [counter(x) for x in self.reactants()]

    def product_list(self):
        return [counter(x) for x in self.products()]


root = tk.Tk()
root.title('Eulerinator')
app = Application(master=root)

root.mainloop()
