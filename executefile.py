import os

from ch4analysis import Dataconverter

def main():

    while True:
        gas = input('Which gas do you want to work with?  ')

        conv = Dataconverter(gas)

        choice = input('Which database do you wish to access:\n'
                       '(1) NOAA or (2) AGAGE ? \n')

        if choice == '1':

            locfile = gas + '_' + 'brw_surface-flask_1_ccgg_month.txt'

            local = os.path.exists('./datasets/')

            if not os.path.exists('./datasets'):

                os.makedirs('./datasets')

            if not os.path.exists('./datasets/surface/' + locfile):

                print('About to download the datasets.\n')
                conv.rollingaccess()

            localchoice = input('Do you want to analyse a single station (1) '
            'or all of them? (2) *Still in development* ')

            if localchoice == '1':

                file = conv.localaccess(gas)
                noaawhole = conv.converter(file)
                noaa_mean, noaapoly = conv.polynom(noaawhole)


            elif localchoice == '2':

                noaawhole, noaa_mean, noaapoly = conv.locfind()


        elif choice == '2':

            agage_whole, agage_mean, agage_trend = conv.agageimport()
            conv.detrender(agage_whole)
            conv.amplitude()
            #conv.plotting(agage_whole, agage_mean, agage_trend)
            #plt.show()

        while True:

            plotchoice = input('Would you like to plot a time of series of the gas (1) '
            ', a change in seasonal amplitude (2) or a yearly change plot (3)? \n')

            if plotchoice == '1':

                conv.plotting(noaawhole, noaa_mean, noaapoly)

            elif plotchoice == '2':

                conv.detrender(noaawhole)
                conv.amplitude()

            elif plotchoice == '3':

                conv.detrender(noaawhole)
                conv.yearavg()

            elif plotchoice == '4':

                break

main()
