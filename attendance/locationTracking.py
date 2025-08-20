# main.py
from kivy.app import App
from kivy.uix.togglebutton import ToggleButton
from kivy.clock import Clock
from plyer import gps
import requests

API_URL = "https://example.com/api/location"  # replace with your API

class LocationApp(App):
    def build(self):
        self.is_sending = False
        self.toggle = ToggleButton(text="Send Location: OFF", size_hint=(.5, .2), pos_hint={"center_x": .5, "center_y": .5})
        self.toggle.bind(on_press=self.toggle_tracking)

        # Setup GPS
        try:
            gps.configure(on_location=self.on_location, on_status=self.on_status)
        except NotImplementedError:
            self.toggle.text = "GPS not supported on this device"
        return self.toggle

    def toggle_tracking(self, instance):
        if self.is_sending:
            # stop sending
            self.is_sending = False
            self.toggle.text = "Send Location: OFF"
            gps.stop()
        else:
            # start sending
            self.is_sending = True
            self.toggle.text = "Send Location: ON"
            gps.start(minTime=1000, minDistance=0)  # update every second

    def on_location(self, **kwargs):
        if self.is_sending:
            lat = kwargs.get('lat')
            lon = kwargs.get('lon')
            data = {"latitude": lat, "longitude": lon}
            try:
                requests.post(API_URL, json=data, timeout=5)
                print(f"Sent: {data}")
            except Exception as e:
                print("Failed to send:", e)

    def on_status(self, stype, status):
        print("GPS Status:", stype, status)


if __name__ == "__main__":
    LocationApp().run()
