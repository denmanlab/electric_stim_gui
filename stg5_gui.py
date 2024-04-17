"""
TITLE: STG5 GUI
DESIGNED BY EASHAN SAHAI
GOAL: USE PYTHON AND A PANEL GUI TO CONTROL ALL FUNCTIONALITY OF THE MCS STG5
NOTES:
The following program uses Panel to allow the users to control the basic Stimulation
Parameters in a given train, the number of trains, delay between trains, and external
signal sent from a given channel
"""

import param
import panel as pn
import numpy as np
import holoviews as hv
import pandas as pd
from panel.template import DarkTheme
from holoviews import opts
import csv
import pendulum
import time
import os
import clr

from System import Action
from System import *

#change this path to the McsUsbNet for your computer
clr.AddReference(r"C:\Users\denma\Documents\GitHub\McsUsbNet_Examples-master\McsUsbNet\x64\McsUsbNet.dll")

from Mcs.Usb import CMcsUsbListNet
from Mcs.Usb import DeviceEnumNet

from Mcs.Usb import CStg200xDownloadNet
from Mcs.Usb import McsBusTypeEnumNet
from Mcs.Usb import STG_DestinationEnumNet

# Set the rendering backend to Bokeh (default)
hv.extension('bokeh')
pn.extension('katex')

# Define a base class for each pipeline stage to handle output updates centrally
class PipelineStage(param.Parameterized):
    @staticmethod
    def update_output(*args, **kwargs):
        # This method will be overridden in the specific implementation for the output tab
        pass

# Stimulation Parameters with pipeline-like dependencies
class StimulationParameters(PipelineStage):
    waveform = param.Selector(default='Biphasic', objects=['Monophasic', 'Biphasic', 'Sinusoidal'], label='Choose Waveform: ')
    volt_or_curr = param.Selector(default='Current', objects=['Current', 'Voltage'], precedence = 0, label='Current or Voltage: ')
    amplitude = param.Number(default=0, label = 'Set Amplitude (uA or uV): ')
    pulse_duration = param.Number(default=100, step=1, label="Set Pulse Duration (us)")
    frequency_or_period_choice = param.Selector(default="Frequency", objects=["Frequency", "Period"], precedence=-1, label = 'Choose Frequency (Hz) or Period (ms): ')  # Visibility controlled by waveform and amplitude
    frequency_period_value = param.Number(default=1.0, step=0.00001, precedence=-1, label = 'Frequency/Period Value: ')  # Visibility controlled by waveform and amplitude, bounds adjusted
    phase = param.String(default='Neither', label = 'Phase Chosen: ')  # Updated based on amplitude
    frequency = param.Number(default=0, bounds=(0, None), label='Current Frequency (Hz): ')  # Dynamically calculated, visibility controlled
    period = param.Number(default=0, bounds=(0, None), label = 'Current Period (ms): ')  # Dynamically calculated, visibility controlled

    def __init__(self, **params):
        super().__init__(**params)
        self._update_phase_text()
        self._update_visibility()

    @param.depends('amplitude', watch=True)
    def _update_phase_text(self):
        if self.amplitude > 0:
            self.phase = "Anode"
        elif self.amplitude < 0:
            self.phase = "Cathode"
        else:
            self.phase = "Neither"

    @param.depends('frequency_or_period_choice', 'frequency_period_value', watch=True)
    def _update_frequency_period(self):
        if self.frequency_or_period_choice == "Frequency":
            self.frequency = self.frequency_period_value
            self.period = (1 / self.frequency_period_value)*1000 if self.frequency_period_value else float('inf')
        else:
            self.period = self.frequency_period_value
            self.frequency = (1 / self.period) * 1000 if self.period else 0

    @param.depends('waveform', 'amplitude', 'volt_or_curr', watch=True)
    def _update_visibility(self):
        is_sinusoidal = self.waveform == 'Sinusoidal' and self.amplitude != 0
        self.param.frequency_or_period_choice.precedence = 1 if is_sinusoidal else -1
        self.param.frequency_period_value.precedence = 1 if is_sinusoidal else -1
        self.param.pulse_duration.precedence = -1 if is_sinusoidal else 1
        self.param['phase'].precedence = 1 if self.waveform == 'Biphasic' else -1  # Hide phase if not Biphasic
        self.param['frequency'].precedence = 1 if self.waveform == 'Sinusoidal' else -1  # Hide phase if not Sinusoidal
        self.param['period'].precedence = 1 if self.waveform == 'Sinusoidal' else -1  # Hide phase if not Sinusoidal

    @param.depends('waveform', 'volt_or_curr', 'amplitude', 'frequency_or_period_choice', 'frequency_period_value', watch=True)
    def view(self):
        waveform_widget = pn.widgets.RadioButtonGroup(name='Waveform', options=self.param['waveform'].objects, value=self.waveform)
        vc_widget = pn.widgets.RadioButtonGroup(name='Current or Voltage', options=self.param['volt_or_curr'].objects, value=self.volt_or_curr)
        amplitude_widget = pn.widgets.FloatInput(name='Amplitude (uA)', value=self.amplitude, step=1)
        phase_display = pn.pane.Markdown(f"**Phase:** {self.phase}", visible=self.waveform == 'Biphasic' and self.amplitude != 0)
        
        frequency_or_period_widget = pn.widgets.RadioButtonGroup(name='Frequency or Period', options=['Frequency', 'Period'], value=self.frequency_or_period_choice, visible=self.waveform == 'Sinusoidal' and self.amplitude != 0)
        frequency_period_value_widget = pn.widgets.FloatInput(name='Frequency/Period Value', value=self.frequency_period_value, visible=self.waveform == 'Sinusoidal' and self.amplitude != 0)
        
        frequency_display = pn.pane.Markdown(f"**Frequency:** {self.frequency} Hz", visible=self.waveform == 'Sinusoidal' and self.amplitude != 0)
        period_display = pn.pane.Markdown(f"**Period:** {self.period} ms", visible=self.waveform == 'Sinusoidal' and self.amplitude != 0)

        return pn.Column(
            waveform_widget,
            vc_widget,
            amplitude_widget,
            phase_display,
            frequency_or_period_widget,
            frequency_period_value_widget,
            pn.layout.Spacer(height=10),  # Add space before frequency/period displays
            frequency_display,
            period_display
        )

# Trigger Parameters with pipeline-like dependencies
class TriggerParameters(PipelineStage):
    allow_external = param.Boolean(False, label='Allow For External Trigger?')
    total_trains = param.Number(default=50, precedence=1, label='Total Number of Trains: ')
    time_between_trains = param.Number(default=2000, precedence=1, label = 'Time Between Each Train (ms):')

    @param.depends('allow_external', watch=True)
    def _update_fields(self):
        if self.allow_external:
            self.param['total_trains'].precedence = -1  # Hide if external is allowed
            self.param['time_between_trains'].precedence = -1
        else:
            self.param['total_trains'].precedence = 1
            self.param['time_between_trains'].precedence = 1
    
    def view(self):
        external_widget = pn.widgets.Toggle(name='Allow External Trigger?', button_type='success')
        total_trains_widget = pn.widgets.IntInput(name='Total Trains', value=self.total_trains)
        time_between_trains_widget = pn.widgets.IntInput(name='Time Between trains (ms)', step=1)

        widgets = pn.Column(external_widget, total_trains_widget, time_between_trains_widget)
        return widgets

# External Signal Parameters
class ExternalSignal(PipelineStage):
    duration = param.Number(default=0.0, label= 'Duration of External Signal (us):')
    delay = param.Number(default=0.0, label='Delay Between External Signal and Stimulation (us):')
    
    def view(self):
        duration_widget = pn.widgets.FloatInput(name='Duration of External Signal (us)', value=self.duration)
        delay_widget = pn.widgets.FloatInput(name='Delay Between External Pulse and Stimulus (us)', value=self.delay)

        widgets = pn.Column(duration_widget, delay_widget)
        return widgets
    
class OutputDisplay(param.Parameterized):
    include_waveform = param.Boolean(True, doc="Include Waveform")
    include_vc = param.Boolean(True, doc="Include VC")
    include_amplitude = param.Boolean(True, doc="Include Amplitude")
    include_pulse_duration = param.Boolean(True, doc="Include Pulse Duration")
    include_phase = param.Boolean(True, doc="Include Phase")
    include_frequency_period_value = param.Boolean(True, doc="Include Frequency/Period Value")
    include_calculated_frequency = param.Boolean(True, doc="Include Calculated Frequency")
    include_calculated_period = param.Boolean(True, doc="Include Calculated Period")
    include_external_triggering = param.Boolean(True, doc="Include External Triggering")
    include_total_trains = param.Boolean(True, doc="Include Total Trains")
    include_time_between_trains = param.Boolean(True, doc="Include Time Between Trains")
    include_external_signal_duration = param.Boolean(True, doc="Include External Signal Duration")
    include_delay_from_beginning = param.Boolean(True, doc="Include Delay From Beginning")
    include_comment = param.String(default='None', doc="Comment")
    output_location = param.String(default='/Users/eashan/DenmanLab/stg5_try/output_1.dat', doc="Output Location")
    run_action = param.Action(label='Run Simulation')


    def __init__(self, stimulation_params, trigger_params, external_signal_params, **params):
        super(OutputDisplay, self).__init__(**params)
        self.stimulation_params = stimulation_params
        self.trigger_params = trigger_params
        self.external_signal_params = external_signal_params
        self.param.watch(self.update_table_data, [
            'include_waveform', 'include_vc', 'include_amplitude', 'include_pulse_duration', 'include_phase', 
            'include_frequency_period_value', 'include_calculated_frequency', 'include_calculated_period',
            'include_external_triggering', 'include_total_trains', 'include_time_between_trains',
            'include_external_signal_duration', 'include_delay_from_beginning'
        ])

    def update_table_data(self, event=None):
        data = {
            "Parameter": [],
            "Value": []
        }

        # Dynamically add data based on the inclusion flags
        if self.include_waveform:
            data["Parameter"].append("Waveform")
            data["Value"].append(self.stimulation_params.waveform)
        if self.include_vc:
            data["Parameter"].append("Voltage or Current")
            data["Value"].append(self.stimulation_params.volt_or_curr)
        if self.include_amplitude:
            data["Parameter"].append("Amplitude")
            data["Value"].append(f"{self.stimulation_params.amplitude} uA")
        if self.include_pulse_duration:
            data["Parameter"].append("Pulse Duration")
            data["Value"].append(f"{self.stimulation_params.pulse_duration} us")
        if self.include_phase:
            data["Parameter"].append("Phase")
            data["Value"].append(self.stimulation_params.phase)
        if self.include_frequency_period_value:
            data["Parameter"].append(self.stimulation_params.frequency_or_period_choice)
            data["Value"].append(self.stimulation_params.frequency_period_value)
        if self.include_calculated_frequency:
            data["Parameter"].append("Calculated Frequency")
            data["Value"].append(f"{self.stimulation_params.frequency} Hz")
        if self.include_calculated_period:
            data["Parameter"].append("Calculated Period")
            data["Value"].append(f"{self.stimulation_params.period} ms")
        if self.include_external_triggering:
            external_triggering = "Yes" if self.trigger_params.allow_external else "No"
            data["Parameter"].append("External Triggering")
            data["Value"].append(external_triggering)
        if self.include_total_trains:
            data["Parameter"].append("Total Trains")
            data["Value"].append(self.trigger_params.total_trains)
        if self.include_time_between_trains:
            data["Parameter"].append("Time Between Trains")
            data["Value"].append(f"{self.trigger_params.time_between_trains} ms")
        if self.include_external_signal_duration:
            data["Parameter"].append("External Signal Duration")
            data["Value"].append(f"{self.external_signal_params.duration} us")
        if self.include_delay_from_beginning:
            data["Parameter"].append("Delay From Beginning")
            data["Value"].append(f"{self.external_signal_params.delay} us")
        if self.include_comment:
            data["Parameter"].append("Comments:")
            data["Value"].append(f"{self.include_comment}")
        # Create DataFrame and update the table
        self.df = pd.DataFrame(data)
        self.table.object = self.df  # Assuming self.table is a pn.widgets.DataFrame or similar
    def _update_output_location(self, event):
        self.output_location = event.new
    def _update_comment_location(self, event):
        self.include_comment = event.new

    def view(self):
        comment_widget = pn.widgets.TextInput(value=self.include_comment, name='Comment: ')
        output_location_widget = pn.widgets.TextInput(value=self.output_location, name='Output Location')
        self.param.output_location = output_location_widget.value  # This line is not necessary; just showing the association
        self.table = pn.pane.DataFrame(pd.DataFrame(), index=False)
        self.update_table_data()  # Populate the table with initial data
        output_location_widget.param.watch(self._update_output_location, 'value')
        comment_widget.param.watch(self._update_comment_location, 'value')
        self.loading_bar_widget = pn.indicators.Progress(name='Progress', value=0,max=100, width=200)
        self.loading_percent = pn.indicators.Number(name='Progress', value=0, format='{value}%')

        # Now include this widget in your layout
        layout = pn.Column(
            self.table,
            pn.layout.Divider(),
            *[
                pn.widgets.Checkbox(name=self.param[p].doc, value=getattr(self, p))
                for p in self.param if isinstance(self.param[p], param.Boolean)
            ],
            comment_widget,
            output_location_widget,  # Include the widget here
            pn.widgets.Button(name="RUN", button_type="primary", on_click=self.run_simulation),
            self.loading_bar_widget,
            self.loading_percent
        )
        return layout
    def create_dat_file(self, file_path, channels_data):
        with open(file_path, 'w') as file:
            # Write header information
            file.write("Multi Channel Systems MC_Stimulus II\n")
            file.write("ASCII import Version 1.10\n\n")
            file.write(f"channels:\t{int(len(channels_data)/2)}\n")
            file.write("output mode:\tcurrent\n")
            file.write("format:\t5\n\n")
            
            # Iterate over each channel and its data
            for channel, data in channels_data.items():
                file.write(f"channel: {channel}\n")
                file.write("pulse\tvalue\tvalue\ttime\n")
                for row in data:
                    file.write(f"{row['pulse']}\t{row['value1']}\t{row['value2']}\t{row['time']}\n")
                file.write("\n")  # Add an empty line after each channel's data
    """
    def channel_data(self, waveform, amplitude, pulse_duration, frequency, total_trains, time_between_trains, external_signal_dur, delay_from_stim):
        channels_data = {1: [], 2:[], 3: [], 4: [], 5: [], 6:[], 7: [], 8: [], 9: [], 10:[], 11: [], 12: [], 13: [], 14:[], 15: [], 16: []}
        
        # Helper function to add pulse data, formatting value1 and value2 as strings with three decimal places
        def add_pulse_data(channel, pulse, value1, value2, time):
            channels_data[channel].append({
                "pulse": pulse,
                "value1": "%.3f" % value1,
                "value2": "%.3f" % value2,
                "time": time  # Leave time as calculated or assigned
            })
        
        # Initial delay for channel 1 and initial signal for channel 3
        add_pulse_data(1, 0, 0.000, 0.000, 5050)  # Initial delay for channel 1
        add_pulse_data(9, 0, 0.000, 0.000, 5050)  # Initial delay for channel 9
        add_pulse_data(10, 0, 0.000, 1.000, 5000)  # Initial 5000 time unit on signal for channel 3
        add_pulse_data(10, 0, 0.000, 0.000, 50)    # Followed by 50 time unit off signal for channel 3
        
        # Calculate pulse time based on waveform
        if waveform == "sinusoidal":
            pulse_time = 1 / frequency
            pulse = 2
        else:  # monophasic or biphasic
            pulse_time = pulse_duration
            pulse = 0
        
        for train in range(total_trains):
            # Channel 1
            #print(train)
            if waveform == "Monophasic":
                add_pulse_data(1, pulse, 0.000, amplitude, pulse_time)
                #print(pulse, amplitude)
            elif waveform == "Biphasic":
                add_pulse_data(1, pulse, 0.000, amplitude, pulse_duration)
                add_pulse_data(1, pulse, 0.000, -amplitude, pulse_duration)
                #print(pulse, amplitude)
            elif waveform == "Sinusoidal":
                add_pulse_data(1, pulse, 0.000, amplitude, pulse_time)
                #print(pulse, amplitude)
            
            # Rest period after each train for channel 1
            if waveform == "Monophasic":
                rest_time = time_between_trains - pulse_time
            elif waveform == "Biphasic":
                rest_time = time_between_trains - (pulse_time * 2)
            elif waveform == "Sinusoidal":
                rest_time = time_between_trains - (1 / frequency)

            add_pulse_data(1, 0, 0.000, 0.000, rest_time)
            
            # Channel 3 - Delay from stim and external signal duration for each train
            if train == 0:  # Only add delay for the first train
                add_pulse_data(9, 0, 0.000, 0.000, delay_from_stim)
            add_pulse_data(9, 0, 0.000, 1.000, external_signal_dur)
            
            # Rest period after external signal for channel 3
            rest_time_3 = time_between_trains - external_signal_dur - delay_from_stim
            add_pulse_data(9, 0, 0.000, 0.000, rest_time_3)
        
        return channels_data
        """
    def channel_data(self, volt_or_curr, waveform, amplitude, pulse_duration, frequency, total_trains, time_between_trains, external_signal_dur, delay_from_stim):
        # Initialize lists to hold amplitude and duration values, and repeat counts
        amplitudes = []
        durations = []
        repeats = []
        syncout_val = []
        syncout_dur = []
        
        # Calculate the base amplitude and duration for each waveform type
        if waveform == "Monophasic":
            # For Monophasic, we have a single phase of stimulation
            amplitudes.extend([amplitude,0])  # Amplitude in uA
            durations.extend([pulse_duration,time_between_trains-pulse_duration])  # Duration in us
            syncout_val.extend([1,0])
            syncout_dur.extend([external_signal_dur, time_between_trains-external_signal_dur])

        elif waveform == "Biphasic":
            # For Biphasic, we have two phases: positive and negative
            amplitudes.extend([amplitude, -amplitude,0])  # Positive then negative phase
            durations.extend([pulse_duration, pulse_duration, time_between_trains-(2*pulse_duration)])  # Same duration for both phases
            syncout_val.extend([1,1,0])
            syncout_dur.extend([int(external_signal_dur/2),int(external_signal_dur-int(external_signal_dur/2)), time_between_trains-external_signal_dur])

        elif waveform == "Sinusoidal":
            # For Sinusoidal, this is an approximation, as actual sinusoidal waveforms
            # would need continuous variation rather than discrete steps
            # Here, you might need a different approach for a true sinusoidal pattern
            # For simplicity, let's treat it as a single phase here
            amplitudes.extend([amplitude,0])  # Amplitude in uA
            pulse_time = 1000 / frequency  # Convert frequency to period (ms), then to us
            durations.append([pulse_time, time_between_trains-pulse_duration])  # Duration in us based on frequency
            syncout_val.extend([1,0])
            syncout_dur.extend([external_signal_dur, time_between_trains-external_signal_dur])

        # Handle repeats - Assuming each pattern is repeated 'total_trains' times
        # This is a simplification; actual implementation might need adjustment
        repeats = [total_trains, 0, 0, 0]  # Repeat each pattern 'total_trains' times
        
        # Convert lists to arrays suitable for STG device programming
        amplitude_arr = amplitudes  # Directly usable in your STG programming function
        duration_arr = durations  # Directly usable in your STG programming function
        repeat_arr = repeats  # Directly usable in your STG programming function
        sync_out_val_arr = syncout_val
        sync_out_dur_arr = syncout_dur
        print(repeat_arr)
        return volt_or_curr, amplitude_arr, duration_arr, repeat_arr, sync_out_val_arr, sync_out_dur_arr
    
    def stg5_connect_and_program(self, volt_or_curr, amplitude_arr, duration_arr, repeat_arr, sync_out_val_arr, sync_out_dur_arr):
    # Placeholder for actual connection logic
        def PollHandler(status, stgStatusNet, index_list):
            print('%x %s' % (status, str(stgStatusNet.TiggerStatus[0])))

        deviceList = CMcsUsbListNet(DeviceEnumNet.MCS_DEVICE_USB)

        print("found %d devices" % (deviceList.Count))

        for i in range(deviceList.Count):
            listEntry = deviceList.GetUsbListEntry(i)
            print("Device: %s   Serial: %s" % (listEntry.DeviceName,listEntry.SerialNumber))


            device = CStg200xDownloadNet();

            device.Stg200xPollStatusEvent += PollHandler;

            device.Connect(deviceList.GetUsbListEntry(0))

            #voltageRange = device.GetVoltageRangeInMicroVolt(0);
            #voltageResulution = device.GetVoltageResolutionInMicroVolt(0);
            #currentRange = device.GetCurrentRangeInNanoAmp(0);
            #currentResolution = device.GetCurrentResolutionInNanoAmp(0);

            #print('Voltage Mode:  Range: %d mV  Resolution: %1.2f mV' % (voltageRange/1000, voltageResulution/1000.0))
            #print('Current Mode:  Range: %d uA  Resolution: %1.2f uA' % (currentRange/1000, currentResolution/1000.0))

            channelmap = Array[UInt32]([1,0,0,0])
            syncoutmap = Array[UInt32]([1,0,0,0])
            start_channelmap = Array[UInt32]([2,0,0,0])
            start_syncoutmap = Array[UInt32]([2,0,0,0])
            start_repeat = Array[UInt32]([1,0,0,0])
            repeat = Array[Int32](repeat_arr)
            amplitude = Array[Int32](amplitude_arr)
            duration = Array[UInt64](duration_arr)
            syncout = Array[Int32](sync_out_val_arr)
            syncout_dur = Array[UInt64](sync_out_dur_arr)
            syncout_start = Array[Int32]([1,0])
            syncout_start_dur = Array[UInt64]([500,100])
            print(channelmap, syncoutmap,start_channelmap,start_syncoutmap)
            device.SetupTrigger(0, channelmap, syncoutmap, repeat)
            device.SetupTrigger(1, start_channelmap, start_syncoutmap, start_repeat)
            if volt_or_curr == 'Current':
                device.SetCurrentMode()
                print('Current Mode')
                device.PrepareAndSendData(0, amplitude*1000, duration, STG_DestinationEnumNet.channeldata_current)
            else:
                device.SetVoltageMode()
                print('Voltage Mode')
                device.PrepareAndSendData(0, amplitude, duration, STG_DestinationEnumNet.channeldata_voltage)

            device.PrepareAndSendData(0, syncout, syncout_dur, STG_DestinationEnumNet.syncoutdata)
            device.PrepareAndSendData(1, syncout_start, syncout_start_dur, STG_DestinationEnumNet.syncoutdata)
            print('Starting!')
            device.SendStart(2)
            time.sleep(0.001)
            print('Sending Pulses!')
            device.SendStart(1)
            tic = time.perf_counter()
            toc = 0
            #time.sleep((np.sum(duration_arr)/1000000)*np.max(repeat_arr))
            total_duration = int((np.sum(duration_arr)/1000000)*np.max(repeat_arr))
            
            while toc < total_duration:
                toc = time.perf_counter()-tic
                #print(toc)
                self.loading_bar_widget.value=int((toc/total_duration)*100)
                self.loading_percent.value = int((toc/total_duration)*100)
                self.update_table_data()
                #print('Updated')
            print('All Done!')
            device.Disconnect()
            print('Disconnected')
    
    def run_simulation(self, event=None):
        # Gather input values from the GUI
        datetime_val = pendulum.now(tz='America/Denver')

        waveform = self.stimulation_params.waveform
        volt_or_curr = self.stimulation_params.volt_or_curr
        amplitude = self.stimulation_params.amplitude
        pulse_duration = self.stimulation_params.pulse_duration
        frequency = self.stimulation_params.frequency  # Use the calculated frequency
        total_trains = self.trigger_params.total_trains
        time_between_trains = self.trigger_params.time_between_trains * 1000  # Convert from ms to us
        external_signal_dur = self.external_signal_params.duration
        delay_from_stim = self.external_signal_params.delay
        
        # Map GUI inputs to channel_data function parameters
        volt_or_curr, amplitude_arr, duration_arr, repeat_arr, sync_out_val_arr, sync_out_dur_arr = self.channel_data(volt_or_curr, waveform, amplitude, pulse_duration, frequency, total_trains, time_between_trains, external_signal_dur, delay_from_stim)
        print(np.shape(amplitude_arr), np.shape(duration_arr), np.shape(repeat_arr), np.shape(sync_out_val_arr), np.shape(sync_out_dur_arr))
        self.stg5_connect_and_program(volt_or_curr, amplitude_arr, duration_arr, repeat_arr, sync_out_val_arr, sync_out_dur_arr)
        #print(waveform, amplitude, pulse_duration, frequency, total_trains, time_between_trains, external_signal_dur, delay_from_stim)
        # Specify the output file path from the GUI input
        #output_file_path = "/Users/eashan/DenmanLab/stg5_try/ascii_output/output_{}-{}-{}T{}_{}.dat".format(datetime_val.year, datetime_val.month, datetime_val.day, datetime_val.hour, datetime_val.minute)
        csv_file_path = r'C:\Users\denma\Desktop\stg5_trial_csvs\csv_{}.csv'.format(datetime_val.to_iso8601_string().replace(':','-').replace('T','_').replace('.','___'))
        
        # Call the function to create and save the .dat file
        #self.create_dat_file(output_file_path, channels_data)
        
    # Save the DataFrame to a CSV file
        self.df.to_csv(csv_file_path, index=False)

        #print(f"Simulation run and data saved to {output_file_path}")
        self.update_table_data()  # Update table data if needed
"""
class GraphicalDisplay(param.Parameterized):
    include_waveform = param.Boolean(True, doc="Include Waveform")
    include_vc = param.Boolean(True, doc="Include VC")
    include_amplitude = param.Boolean(True, doc="Include Amplitude")
    include_pulse_duration = param.Boolean(True, doc="Include Pulse Duration")
    include_phase = param.Boolean(True, doc="Include Phase")
    include_frequency_period_value = param.Boolean(True, doc="Include Frequency/Period Value")
    include_calculated_frequency = param.Boolean(True, doc="Include Calculated Frequency")
    include_calculated_period = param.Boolean(True, doc="Include Calculated Period")
    include_external_triggering = param.Boolean(True, doc="Include External Triggering")
    include_total_trains = param.Boolean(True, doc="Include Total Trains")
    include_time_between_trains = param.Boolean(True, doc="Include Time Between Trains")
    include_external_signal_duration = param.Boolean(True, doc="Include External Signal Duration")
    include_delay_from_beginning = param.Boolean(True, doc="Include Delay From Beginning")
    include_comment = param.String(default='None', doc="Comment")
    output_location = param.String(default='/Users/eashan/DenmanLab/stg5_try/output_1.dat', doc="Output Location")
    run_action = param.Action(label='Run Simulation')

    # Define a function to generate the desired waveform
    def generate_waveform(waveform_type, amplitude=1, pulse_length=0.1, delay=0.1, frequency=1, cathode_first=True):
        time = np.linspace(0, 2, 1000)  # 2 seconds duration, 1000 points
        signal = np.zeros_like(time)
        
        if waveform_type == 'Monophasic':
            pulse_end = pulse_length
            signal[(time >= delay) & (time <= pulse_end + delay)] = amplitude
        elif waveform_type == 'Biphasic':
            pulse_end = 2 * pulse_length
            if cathode_first:
                signal[(time >= delay) & (time < pulse_length + delay)] = amplitude
                signal[(time >= pulse_length + delay) & (time <= pulse_end + delay)] = -amplitude
            else:
                signal[(time >= delay) & (time < pulse_length + delay)] = -amplitude
                signal[(time >= pulse_length + delay) & (time <= pulse_end + delay)] = amplitude
        elif waveform_type == 'sine':
            signal = amplitude * np.sin(2 * np.pi * frequency * time)
        
        return hv.Curve((time, signal), 'Time (s)', 'Amplitude').opts(width=700, height=400, ylim=(-2, 2))

    # Create interactive widgets
    waveform_type = pn.widgets.Select(name='Waveform Type', options=['monophasic', 'biphasic', 'sine'])
    amplitude = pn.widgets.FloatSlider(name='Amplitude', start=0.1, end=2, step=0.1, value=1)
    pulse_length = pn.widgets.FloatSlider(name='Pulse Length (s)', start=0.05, end=0.5, step=0.05, value=0.1)
    delay = pn.widgets.FloatSlider(name='Delay (s)', start=0, end=1, step=0.1, value=0.1)
    frequency = pn.widgets.FloatSlider(name='Frequency (Hz)', start=0.5, end=10, step=0.5, value=1)
    cathode_first = pn.widgets.RadioButtonGroup(name='Cathode First', options=[True, False], value=True)

    # Dynamically update the plot based on the widget inputs
    @pn.depends(waveform_type.param.value, amplitude.param.value, pulse_length.param.value, delay.param.value, frequency.param.value, cathode_first.param.value)
    def update_plot(waveform_type, amplitude, pulse_length, delay, frequency, cathode_first):
        return generate_waveform(waveform_type, amplitude, pulse_length, delay, frequency, cathode_first)

    # Layout
    widgets = pn.Column(waveform_type, amplitude, pulse_length, delay, frequency, cathode_first)
    layout = pn.Row(widgets, pn.Column(update_plot))

    # Display the interactive plot
    pn.extension()
    layout.show()
"""
# Instantiate stages
stimulation_params = StimulationParameters()
trigger_params = TriggerParameters()
external_signal_params = ExternalSignal()
output_display = OutputDisplay(stimulation_params, trigger_params, external_signal_params)

# Setting up the tabs
tabs = pn.Tabs(
    ('Stimulation Parameters', pn.Column(stimulation_params)),
    ('Trigger Parameters', pn.Column(trigger_params)),
    ('External Signal', pn.Column(external_signal_params)),
    ('Output', pn.Column(output_display.view))
)

for stage in [stimulation_params, trigger_params, external_signal_params]:
    stage.param.watch(lambda event: output_display.update_table_data(), list(stage.param))

# Servable app
tabs.servable()

tabs.show(port=8080)
