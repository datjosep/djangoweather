import nexradaws
import pytz
import tempfile
from datetime import datetime
from mysite.asgard.forms import data_form
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from mysite.asgard.forms import SignUpForm
from django.http import HttpResponseRedirect
from django.urls import reverse

#import libraries for radar visualization
import numpy as np
import pyart
import boto
import matplotlib as mpl
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
#suppress deprecation warnings
import warnings
warnings.simplefilter("ignore", category=DeprecationWarning)

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect('base.html')
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})


def post_form_upload(request):
    if request.method == 'GET':
        form = data_form()
    else:
        # A POST request: Handle Form Upload
        form = data_form(request.POST)  # Bind data from request.POST into a PostForm

        # If data is valid, proceeds to create a new post and redirect the user
        if form.is_valid():
            site = get_results()
            start_time = get_results()
            end_time = get_results()
            site = form.cleaned_data['radar site']
            start_time = form.cleaned_data['date1']
            end_time = form.cleaned_data['date2']
            return HttpResponseRedirect(reverse('radar site', 'date1','date2',
                                                kwargs={'site': site, 'date1': start_time, 'date2': end_time}))

    return render(request, 'mysite/asgard/radarsite.html', {
        'form': form,
    })

class DataHandling:

    def __init__(self, time_zone):
        self._time_zone = time_zone
        self._startTime = None
        self._endTime = None

    def data(request):
        form_class = data_form

        return render(request, 'radarsite.html', {
            'form': form_class,
        })
    def get_inputs(self):
        # select the radar site
        while True:
            try:
                self._site = input("What is the radar site?")
            except ValueError:
                print("radar site are 4 letters in all caps Ex. KIND")
                continue
            else:
                break
        if len(self._site) != 4 and not self._site.isupper():
            print("Make sure values are typed in correctly")
        else:
            print("Input processes and received, moving on!")
        # Start and end times for data collection.
        while True:
            try:
                start_time = input(
                    "Enter a date in Year, Month, Day, Hr, minute format" "Ex. 2013, 5, 31, 17, 0")
            except ValueError:
                print("Did you input the date in the right format?")
                continue
            else:
                break

        self._startTime = datetime(*map(lambda val: int(val), start_time.split(",")))
        while True:
            try:
                end_time = input("Enter a date in Year, Month, Day, Hr, minute format" "Ex. 2013, 5, 31, 17, 0")
            except ValueError:
                print("Did you input the date in the right format?")
                continue
            else:
                break
        self._endTime = datetime(*map(lambda val: int(val), end_time.split(",")))

        # ...this returns a list of all of the radar sites with data for the selected date

    @property
    def start_time(self):
        return self._time_zone.localize(self._startTime)

    @property
    def end_time(self):
        return self._time_zone.localize(self._endTime)

    @property
    def site(self):
        return self._site


def get_results():
    data_handling = DataHandling(time_zone=pytz.timezone('US/Central'))
    data_handling.get_inputs()
    conn = nexradaws.NexradAwsInterface()
    scans = conn.get_avail_scans_in_range(data_handling.start_time, data_handling.end_time, data_handling.site)
    print("There are {} scans available between {} and {}\n".format(len(scans), data_handling.start_time,
                                                                    data_handling.end_time))
    temp_location = tempfile.mkdtemp()
    results = conn.download(scans[0:], temp_location)
    print(results)


get_results()

# classes, objects, instances, modules, functions.
# basics of OOP
# work and understand every line of this code.
class Visualize:

    def map_results(self):
        "save the nexrad locations to an array from the PyART library"
        locs = pyart.io.nexrad_common.NEXRAD_LOCATIONS
        "set up the figure for plotting"
        fig = plt.figure(figsize=(12,8),dpi=100)
        ax = fig.add_subplot(111)
        "create a basemap for CONUS"
        m = Basemap(projection='lcc',lon_0=-95,lat_0=35.,
           llcrnrlat=20,urcrnrlat=50,llcrnrlon=-120,
           urcrnrlon=-60, resolution='l')
        "draw the geography for the basemap"
        m.drawcoastlines(linewidth=1)
        m.drawcountries(linewidth=1)
        m.drawstates(linewidth=0.5)
        "plot a point and a label for each of the radar site locations within the CONUS domain"
        for key in locs:
            lon = locs[key]['lon']
            lat = locs[key]['lat']
            name = key
            if lon >= -120 and lon <= -60 and lat >= 20 and lat <= 50:
                m.scatter(lon, lat, marker='o', color='b', latlon=True)
                x, y = m(lon+0.2, lat+0.2)
                plt.text(x, y, name, color='k', fontsize=7)
        "create a figure title"
        fig.text(0.5,0.92, 'CONUS NEXRAD locations',horizontalalignment='center')
        plt.show()

        "base map has been fully developed at this time, move on to display data on base map"
        "select the radar site"
        site = get_results()
        "Here I want to fetch the site value that the user inputted from the previous function"

        "get the radar location (this is used to set up the basemap and plotting grid)"
        loc = pyart.io.nexrad_common.get_nexrad_location(site)
        lon0 = loc[1]; lat0 = loc[0]
        "use boto to connect to the AWS nexrad holdings directory"
        s3conn = boto.connect_s3()
        bucket = s3conn.get_bucket('noaa-nexrad-level2')
        "create a datetime object for the current time in UTC and use the"
        "year, month, and day to drill down into the NEXRAD directory structure."
        start_time = get_results()
        """get the bucket list for the selected date
           Note: this returns a list of all of the radar sites with data for
           the selected date"""
        ls = bucket.list(prefix=start_time, delimiter=',')
        for key in ls:
            "only pull the data and save the arrays for the site we want"
            if site in key.name.split(',')[-2]:
                "set up the path to the NEXRAD files"
                path = start_time + site + ',' + site
                "grab the last file in the file list"
                fname = bucket.get_all_keys(prefix=path)[-1]
                "get the file"
                s3key = bucket.get_key(fname)
                "save a temporary file to the local host"
                localfile = tempfile.NamedTemporaryFile(delete=False)
                "write the contents of the NEXRAD file to the temporary file"
                s3key.get_contents_to_filename(localfile.name)
                "use the read_nexrad_archive function from PyART to read in NEXRAD file"
                radar = pyart.io.read_nexrad_archive(localfile.name)
                "get the date and time from the radar file for plot enhancement"
                time = radar.time['units'].split(' ')[-1].split('T')
                print(site + ': ' + time[0] + ' at ' + time[1])

                "set up the plotting grid for the data"
                display = pyart.graph.RadarMapDisplay(radar)
                x, y = display._get_x_y(0, True, None)

        # set up a 1x1 figure for plotting
        fig, axes = plt.subplots(nrows=1, ncols=1, figsize=(9, 9), dpi=100)
        # set up a basemap with a lambert conformal projection centered
        # on the radar location, extending 1 degree in the meridional direction
        # and 1.5 degrees in the longitudinal in each direction away from the
        # center point.
        m = Basemap(projection='lcc', lon_0=lon0, lat_0=lat0,
                    llcrnrlat=lat0 - 1.25, llcrnrlon=lon0 - 1.5,
                    urcrnrlat=lat0 + 1.25, urcrnrlon=lon0 + 1.5, resolution='h')

        # get the plotting grid into lat/lon coordinates
        x0, y0 = m(lon0, lat0)
        glons, glats = m((x0 + x * 1000.), (y0 + y * 1000.), inverse=True)
        # read in the lowest scan angle reflectivity field in the NEXRAD file
        refl = np.squeeze(radar.get_field(sweep=0, field_name='reflectivity'))
        # set up the plotting parameters (NWSReflectivity colormap, contour levels,
        # and colorbar tick labels)
        cmap = 'pyart_NWSRef'
        levs = np.linspace(0, 80, 41, endpoint=True)
        ticks = np.linspace(0, 80, 9, endpoint=True)
        label = 'Radar Reflectivity Factor ($\mathsf{dBZ}$)'
        # define the plot axis to the be axis defined above
        ax = axes
        # normalize the colormap based on the levels provided above
        norm = mpl.colors.BoundaryNorm(levs, 256)
        # create a colormesh of the reflectivity using with the plot settings defined above
        cs = m.pcolormesh(glons, glats, refl, norm=norm, cmap=cmap, ax=ax, latlon=True)
        # add geographic boundaries and lat/lon labels
        m.drawparallels(np.arange(20, 70, 0.5), labels=[1, 0, 0, 0], fontsize=12,
                        color='k', ax=ax, linewidth=0.001)
        m.drawmeridians(np.arange(-150, -50, 1), labels=[0, 0, 1, 0], fontsize=12,
                        color='k', ax=ax, linewidth=0.001)
        m.drawcounties(linewidth=0.5, color='gray', ax=ax)
        m.drawstates(linewidth=1.5, color='k', ax=ax)
        m.drawcoastlines(linewidth=1.5, color='k', ax=ax)
        # mark the radar location with a black dot
        m.scatter(lon0, lat0, marker='o', s=20, color='k', ax=ax, latlon=True)
        # add the colorbar axes and create the colorbar based on the settings above
        cax = fig.add_axes([0.075, 0.075, 0.85, 0.025])
        cbar = plt.colorbar(cs, ticks=ticks, norm=norm, cax=cax, orientation='horizontal')
        cbar.set_label(label, fontsize=12)
        cbar.ax.tick_params(labelsize=11)
        # add a title to the figure
        fig.text(0.5, 0.92, site + ' (0.5$^{\circ}$) Reflectivity\n ' +
                 time[0] + ' at ' + time[1], horizontalalignment='center', fontsize=16)
        # display the figure
        plt.show()

    map_results()

    #Attrib credit: Jonathan J. Helmus - created most of this code to visualize data using Py-ART