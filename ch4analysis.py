import pip, os
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from ftplib import FTP
import requests, os, io, urllib3
from zipfile import ZipFile
from tqdm import tqdm
from pandas.plotting import register_matplotlib_converters

class Dataconverter(object):

    def __init__(self,gas):

        register_matplotlib_converters()
        self.gas = gas

    def localaccess(self, locgas):

        locstation = input ('Which station do you want to work with? (three letter code)  ')
        file = locgas + '_' + locstation + '_surface-flask_1_ccgg_month.txt'

        return file


    def rollingaccess(self):


        ftp = FTP('aftp.cmdl.noaa.gov')   # connect to host, default port
        ftp.login()               # user anonymous, passwd anonymous@
        ftp.cwd('/data/trace_gases/'+ self.gas +'/flask/')        #Change directory

        ls = ftp.nlst()

        for i in ls:

            if self.gas and '.zip' in i:

                print('Starting Download\n')
                ftp.retrbinary('RETR ' + i, open(i, 'wb').write)
                print('Download finished \n')
                ftp.close()

                #Change the folder of the zip file.
                #os.mkdir('./datasets/' + sefl.gas)
                os.rename('./'+ i, './datasets/'+ i)

                print('Unzipping the file\n')
                zip = ZipFile('./datasets/'+i, 'r')
                zip.extractall('./datasets/')
                print('Done.\n')

    def converter(self, file):

        dataset = pd.read_csv('./datasets/surface/'+file, header=None,names=['ppm'], comment='#',
                           parse_dates=True, infer_datetime_format=True,
                           skip_blank_lines=True,dtype='str', engine='python')

        #Separate the import single string into four different columns to ease the work
        datatime = dataset.iloc[:,0].str.split(pat=None, expand=True)  #Split raw data
        datatime.columns = ['stations','year', 'month', 'gas']
        #Insert day in the column (middle of month) to ease transformation into date format
        datatime.insert(3, 'day', 15, True)
        datadate = pd.DataFrame(datatime.iloc[:,1:4])
        datadate.columns = ['year', 'month', 'day']
        date = pd.to_datetime(datadate)
        datatime = datatime.set_index(date)
        #Remove the now useless columns
        datatime.drop(datatime.columns[[0,1,2,3]],1,inplace=True)

        datatime['gas']=datatime.astype(float)  #Turn into float to average it.
        return datatime

    def polynom(self, data):

        year_mean = data.groupby(data.index.year).mean()
        fits = np.polyfit(year_mean.index, year_mean.iloc[:,0], 10)
        trendpoly = np.poly1d(fits)

        return year_mean, trendpoly


    def agage(self):

        station = input('What station does your heart desire? Mace Head (MHD),'
                       'Ragged Point (RPB), Cape Matatula (SMO),Trinidad Head (THD) ')


        r = requests.get('http://agage.eas.gatech.edu/data_archive/agage/gc-md/monthly/'+station+'-gcmd.mon')

        filename = station+'-gcmd.txt'
        data = open(filename, 'w')
        data.write(r.text)
        dataset = pd.read_csv(filename, skip_blank_lines=True, skiprows=15)

        return dataset


    def agageimport(self):


        rawdata = self.agage()
        #Seperate the data columns.
        sepdata = rawdata.iloc[:,0].str.split(pat=None, n=0, expand=True)
        methane = sepdata.iloc[:,22:24].astype(float)   #Separate Methane and error from the rest.

        #Make the same procedure as for NOAA date format
        datadate = pd.DataFrame(sepdata.iloc[:,1:3])
        datadate.insert(0,'day',15, True)
        datadate.columns = ['day', 'month', 'year']
        date = pd.to_datetime(datadate)
        methane = methane.set_index(date)
        methane.columns = ['ch4', 'Error']

        year_mean = methane.groupby(methane.index.year).mean()
        fits = np.polyfit(year_mean.index, year_mean.iloc[:,0], 5)
        trendpoly = np.poly1d(fits)

        return methane, year_mean, trendpoly

    def plotting(self, whole, mean, poly):


        fig = plt.figure()
        ax1 = fig.add_subplot(111)
        ax1.plot(whole.index, whole.iloc[:,0], alpha=0.5, label='Monthly mean')

        #Double y axis to allow the plotting of yearly average that is not in date format
        ax2 = ax1.twiny()

        ax2.plot(mean.index, mean.iloc[:,0], c='black', label='Year average')
        ax2.plot(mean.index, poly(mean.index), c='r', ls='--', label='Polynomial regression')
        #ax2.plot(mean.index, mean.iloc[:,0])
        #ax2.plot(mean.index, poly(mean.index))
        ax1.legend(loc='upper center')
        ax2.legend(loc='upper left')
        plt.ylabel('Concentration')
        plt.xlabel('Time (years)')

        plt.show()


    def detrender(self, monthly):

        midpoint = []
        newmonth = pd.DataFrame(monthly)
        middle = newmonth.index.to_series()

        index = []
        for i in range(len(newmonth)):

            if i < 11:
                index.append(middle[i])
                midpoint.append(np.average(newmonth.iloc[i:i+24,0]))

            if i > 11:
                index.append(middle[i])
                midpoint.append(np.average(newmonth.iloc[i-12:i+12,0]))

            if i > len(monthly)-12:
                index.append(middle[i])
                midpoint.append(np.average(newmonth.iloc[i-24:i,0]))

        rolling = pd.DataFrame(midpoint, index=index, columns=['gas'], dtype=float)

        self.detren = newmonth.iloc[:,0] - rolling.iloc[:,0]
        self.yearly = self.detren.groupby(self.detren.index.year)

    def yearavg(self):


        perchoice1 = float(input('Which period would you like to compare? '
        'enter start of period and then the duration (e.g. 1991 and then 10)'))
        perchoice2 = float(input('\n Length of period?'))

        perchoice3 = float(input('\nWith which one? '))
        perchoice4 = float(input('Length of this period? '))

        for i in self.yearly.groups:
            if perchoice1 <= i <= perchoice1 + perchoice2:
                oldtren = self.yearly.get_group(i)
                plt.scatter(oldtren.index.month, oldtren, c='blue')

            if perchoice3 <=i<= perchoice3 + perchoice4:
                tren = self.yearly.get_group(i)
                plt.scatter(tren.index.month, tren, c='black')
        """
        for i in self.yearly.groups:

            if 1972 <= i <= 1975:

                oldtren = self.yearly.get_group(i)
                plt.scatter(oldtren.index.month, oldtren, c='blue')
                #plt.title('2009 - 2011 Period')

            if 2009 <= i <= 2011:

                tren = self.yearly.get_group(i)
                plt.scatter(tren.index.month, tren, c='black')
                #plt.title('2009 - 2011 Period')

            if 2017 <= i <= 2018:

                newtren = self.yearly.get_group(i)
                plt.scatter(newtren.index.month, newtren, c='red')
                #plt.title('2009 - 2011 Period')
        """
        plt.ylabel('detrended CO2(ppm)')
        plt.xlabel('Months of the year')
        plt.title('Yearly variations')
        plt.show()


    def amplitude(self):

        #Goes through each year group and make the difference between the lowest
        #and highest value to get the amplitude.

        for i in self.yearly.groups:

            maximum = self.detren.groupby(self.detren.index.year).aggregate(np.max)
            minimum = self.detren.groupby(self.detren.index.year).aggregate(np.min)

        amp = maximum - minimum
        plt.plot(amp.index, amp.iloc[:])
        plt.xlabel('Years')
        plt.ylabel('Detrended '+ self.gas)

        plt.show()

    def grouping(self, location):

        #stat = pd.read_csv('statname.txt', dtype='str' ,engine='python', sep='    ')
        #self.stations = stat.iloc[:,0].str.split(pat='\t', expand=True)
        #self.stations.iloc[:,3:5] = self.stations.iloc[:, 3:5].astype(float)

        location.iloc[:,1:2] = location.iloc[:, 1:2].astype(float)

        #latchoice = input("What lattitude do you want to analyse?\n(1) 15-25\n(2) 25-35\n"
        #"(3) 35-45\n(4) 45-55\n(5) 55-65\n (6) 65-75\n (7) 75-90")
        latchoicestart = int(input("First enter the start of the lattitudinal band (e.g. 15 for the 15-25 band, ...): \n  "))
        latchoicend = int(input("\nNow please enter the end of the band (e.g. 25 for the 15-25 band): \n"))
        self.latband = []
        for i in range(len(location)):
            if latchoicestart <= location.iloc[i,1] <= latchoicend:
                self.latband.append(location.iloc[i,0])



    def ranker(self):

            leng = []
            for i in range(len(self.latband)):
                for j in self.dirl:
                    if ((self.gas in j)&(self.latband[i] in j)&('month' in j)&(j[len(self.gas)] == '_')):
                        monthly = self.converter(j)
                        #Rank the datasets for the longest record.
                        leng.append(len(monthly))
                        break

            length = pd.DataFrame(leng,index=self.latband)
            max = length.aggregate(np.max)

            for i in range(len(length.iloc[:,0])):

                if int(length.iloc[i,0]) == int(max):

                    self.latband[i] = self.latband[0]
                    self.latband[0] = length.index[i]



    def locfind(self):

        self.dirl = os.listdir('./datasets/surface/')

        loc, lat, long = [], [], []

        #Goes through all the files in the dataset directory and get details
        #of the stations for latitude and longitude though the .._event.txt file.
        counter = 0

        for i in tqdm(self.dirl, desc='Getting locations'):

            if ((self.gas in i)&('event' in i)&(i[len(self.gas)] == '_')):
                monthfilename = i.replace('event','month')
                monthfile = os.path.isfile('./datasets/surface/' + monthfilename)
                if monthfile == True:

                    file = pd.read_csv('./datasets/surface/'+ i, header=None, comment='#',
                                                   parse_dates=True, infer_datetime_format=True,
                                                   skip_blank_lines=True,dtype='str', engine='python')

                    sepdata = file.iloc[:,0].str.split(pat=None, n=0, expand=True)

                    counter = 0
                    locstring = []
                    for j in range(len(i)):
                        if ((i[j]=='_')&(counter==0)):
                            spot = j
                        if ((i[j]=='_')&(counter<=1)):
                            counter += 1
                        if ((i[j]=='_')&(counter==2)):
                            counter += 1
                            loc.append(i[spot+1:j])

                    lat.append(sepdata.iloc[1, 21])
                    long.append(sepdata.iloc[1, 22])

        locations = pd.DataFrame(list(zip(loc,lat,long)), columns=['Station', 'Lat', 'Long'])
        #Pass the location of the stations to the grouping function to group them
        #into lattitudinal bands.
        self.grouping(locations)

        #The ranker function will rank the data for the longest record to serve as the
        #main dataset to append the other stations to it.
        self.ranker()

        counter = 0

        for i in self.latband:
            for j in self.dirl:
                if ((self.gas in j)&(i in j)&('month' in j)&(j[len(self.gas)] == '_')):

                    monthly = self.converter(j)
                    counter += 1

                    if counter == 1:
                        #Puts the longest record as the record on which to paste the others
                        #that was taken in the ranker function.

                        latdata = monthly

                    if counter > 1:
                        #Append the other data sets from the grouped lat bands onto the main dataset.
                        latdata.insert(counter-1, i, monthly.iloc[:,0])

                    break

        #Average the whole data set, that is, all the stations in the lat band
        avgconcat = latdata.mean(axis=1)
        avgcon = pd.DataFrame(avgconcat)
        #Pass the new dataset into the polynom method.
        conmean, conpoly = self.polynom(avgcon)

        return avgcon, conmean, conpoly
