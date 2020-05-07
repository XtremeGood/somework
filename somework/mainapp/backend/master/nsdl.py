import os
import sqlite3
import pandas as pd
import pickle
import io

from abc import ABCMeta


class Meta1(metaclass=ABCMeta):
    def __init__(self, cols_file, df):
        self.cols = self.get_cols(cols_file)
        self.data = self.get_data(df)

    def get_cols(self, cols_file):
        with open(cols_file, "rb") as p:
            cols = pickle.load(p)
        return cols

    def get_data(self, df):
        return df.loc[:, self.cols]

    def clean(self, data):
        pass


class Dematad(Meta1):

    def __init__(self, cols_file, df):
        super().__init__(cols_file, df)
        self.data = self.clean(self.data)

    def clean(self, data):
        return self.data.drop_duplicates(subset=["DPID", "CLID"], keep='first', inplace=True)


class Demathol(Meta1):
    def __init__(self, cols_file, df):
        super().__init__(cols_file, df)
        #self.data = self.clean(self.data)

    def clean(self, data):
        return self.data.drop_duplicates(subset=["DPID", "CLID"], keep='first', inplace=True)


class PrepareDf:

    def __init__(self, main_cols_loc, dematad_cols_loc, demathol_cols_loc, file_obj):
        cols = self.get_col_names(main_cols_loc)
        table = self.get_table_from_file(file_obj)
        df = self.get_df_from_table(table, cols)

        self.dematad = Dematad(dematad_cols_loc, df)
        self.demathol = Demathol(demathol_cols_loc, df)

    def get_col_names(self, main_cols_loc):
        with open(main_cols_loc, "rb") as p:
            cols = pickle.load(p)
        return cols

    def get_table_from_file(self, file_obj):

        data = file_obj.readlines()
        for k, i in enumerate(data):
            data[k] = i.decode()
        for i in range(1, len(data)):

            if data[i-1].startswith("01") and data[i].startswith("01"):
                data[i-1] = None
            else:
                data[i] = data[i].strip()

        table = list(filter(None, data))

        return table

    def get_df_from_table(self, table, cols):
        i = 0
        pd_data = []
        while i < len(table):
            if table[i].startswith("01"):
                isin, date = table[i].split("##")[1:3]

                data = []
                i += 1
                while i < len(table) and not(table[i].startswith("01")):
                    data.append(table[i].split("##")[2:])
                    i += 1

                temp = pd.DataFrame(data=data, columns=cols)
                temp["ISEN"] = isin
                temp["DATE"] = date
                pd_data.append(temp)

        df = pd.concat(pd_data, ignore_index=True)
        return df


def main(obj):

    df = PrepareDf(os.path.join(os.getcwd(), 'mainapp', 'backend',
                                'master', 'cols', 'cols.pk'),
                   os.path.join(os.getcwd(), 'mainapp', 'backend',
                                'master', 'cols', 'dematad.pk'),
                   os.path.join(os.getcwd(), 'mainapp', 'backend',
                                'master', 'cols', 'demathol.pk'),
                   obj)

    dematad = df.dematad

    demathol = df.demathol
    conn = sqlite3.connect("MASS.db")
