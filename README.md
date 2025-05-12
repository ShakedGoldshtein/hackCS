# FalseBusters - 
This is a POC for TechnionHACK2025 

# Installation:

please download the folder and install it as a chrome extension using development mode.

# Current features:

1. Displays a graph showing locations of "problematic" claims throughout the video, and an indication of the location in the video you are currently vieweing.
2. Locations of problematic claims are shown as dots on the graph, the redder the dot - the more severe the claim is.
3. Clicking directly on a point, will move to a timestamp a few moments before a claim, so you can hear it again.
4. A chime sound will be played as you encounter a problematic claim + a pop up notification displaying it (see image below).
5. Hovering over a dot in the graph also shows a brief explanation about the claim.
6. Plug in settings are adjustabme via the settings menu (colors of all elements can be adjusted, the chime can be turned off and the graph can be hidden).

# How it works behind the scenes:
1. The video is downloaded in the background, and is converted to text via whisper.
2. The text goes thoguth our processing pipeline, which includes extratcing claims, debunking said claimd and checking for logical falacies.
3. The conclusion is then presented as dots on the tineline graph, presented on the screen.


A live demo can be seen here:

https://www.youtube.com/watch?v=tHYybxvNjbY&t=8s&ab_channel=BarTzipori

