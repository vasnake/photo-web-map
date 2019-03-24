# photo-web-map
Web map with geotagged photo and video overlay

It's not a ready-to-use project, it is just a set of scripts (DIY style) created in order to build a serverless SPA: 
web-map based on the Leaflet. This web-map should show clustered markers, 
made from thumbnails from geotagged photo and video
that I took on my trip to USA in year 2018. Click on thumbnail should show full-size photo/video.

Web-map have a filter UI, allowing to show photos and/or videos according to selected date, state, town.
State and town names was produced with 'reverse geocoding' step of the build.

For detailed information about build see script [show.sh](show.sh).
Web-map details you can find in [map.html](map.html).
