T='online'
S='offline'
P='/state'
O=''
N='/system/status'
H='/'
C=str
F=False
E=True
D=None
B=print
import json as K,ubinascii as L,network as J
from umqtt.robust2 import MQTTClient as Q
import machine as G
from machine import Timer as I,Pin,ADC
import time as M
class A:
	def __init__(A,wifi_ssid,wifi_password,mqtt_server,mqtt_port=1883,mqtt_user=D,mqtt_password=D,mqtt_keepalive=1800):N=mqtt_keepalive;K=mqtt_password;H=mqtt_user;E=mqtt_port;C=mqtt_server;A.wifi_ssid=wifi_ssid;A.wifi_password=wifi_password;A.mqtt_server=C;A.mqtt_port=E;A.mqtt_user=H;A.mqtt_password=K;A.mqtt_keepalive=N;A.pico_id='pico-'+L.hexlify(G.unique_id()).decode();A.led=Pin('LED',Pin.OUT);A.wlan=J.WLAN(J.STA_IF);A.mqtt=Q(A.pico_id,C,E,H,K,keepalive=N);A.device_name='ML HA Generic Device';A.enable_temp_sensor=F;A.temp_sensor=F;A.last_temp=0;A.mqtt_callback=D;A.error_count=0;B(A.pico_id);B('ML HA v0.2');B('Checking LED for 5 seconds');A.led.on();M.sleep(5);B('Initializing WiFi');A.connectWifi();B('Initializing MQTT');A.connectMQTT();B('Starting watchdog');A.watchdog=I();A.watchdog.init(period=2500,mode=I.PERIODIC,callback=A.watchdog_cb);B('ML HA Initialized')
	def toggle_led(A,t):A.led.toggle()
	def connectWifi(A):
		A.wlan.active(E);A.wlan.connect(A.wifi_ssid,A.wifi_password);D=30;F=I();F.init(freq=3,mode=I.PERIODIC,callback=A.toggle_led)
		while A.wlan.status()!=3:
			B('Waiting, wlan status '+C(A.wlan.status()));D-=1
			if D==0:B('Failed to connect to WiFi');G.reset()
			M.sleep(1)
		B('Connected, wlan status '+C(A.wlan.status()));H=A.wlan.ifconfig();B('connected as '+H[0]);F.deinit();A.led.off()
	def watchdog_cb(A,t):
		if A.error_count>10:B('MQTT connection lost, resetting');G.reset()
		if A.mqtt.is_conn_issue():B('MQTT connection issue, count: '+C(A.error_count));A.error_count+=1;A.mqtt.disconnect();A.mqtt.reconnect();A.mqtt.resubscribe()
		else:A.error_count=0
	def connectMQTT(A):A.mqtt.set_last_will(A.pico_id+N,S,retain=E);A.mqtt.connect();A.mqtt.DEBUG=E;A.mqtt.KEEP_QOS0=F;A.mqtt.NO_QUEUE_DUPS=E;A.mqtt.MSG_QUEUE_MAX=2;A.mqtt.set_callback(A.sub_cb)
	def sub_cb(A,topic,msg,retained,duplicate):
		G=duplicate;F=retained;E=topic;A.led.on();B('Received message on topic '+E.decode()+'( '+C(F)+'|'+C(G)+' )'+': '+msg.decode())
		if A.mqtt_callback is not D:A.mqtt_callback(E.decode().replace(A.pico_id+H,O),msg,F,G)
		A.led.off()
	def set_callback(A,callback):A.mqtt_callback=callback
	def subscribe(A,topic,absolute=F):
		B=topic
		if absolute:A.mqtt.subscribe(B)
		else:A.mqtt.subscribe(A.pico_id+H+B)
	def publish(A,topic,msg,retain=F):A.mqtt.publish(b''+A.pico_id+H+topic,msg,retain)
	def set_device_name(A,name):A.device_name=name
	def set_enable_temp_sensor(A,bool):A.enable_temp_sensor=bool
	def update_temp_sensor(A):
		D='_temperature'
		if A.enable_temp_sensor:
			if not A.temp_sensor:A.temp_sensor=G.ADC(4);A.publish_config(A.device_name+D,A.device_name+' Temperature',device_class='temperature',unit_of_measurement='C',state_class='measurement',state_topic=H+A.device_name+D,expire_after=300)
			E=A.temp_sensor.read_u16()*(3.3/65535);B=round(27-(E-0.706)/0.001721,2)
			if A.last_temp!=B:A.last_temp=B;A.publish(A.device_name+D+P,C(B))
	def publish_config(C,discovery_topic,name,device_type='sensor',device_class=D,unit_of_measurement=D,state_class=D,state_topic=O,expire_after=60):
		b='payload_off';a='payload_on';Z='mac';Y='state_class';X='unit_of_measurement';W='value_template';V='device_class';U='name';R=state_topic;Q=state_class;M=unit_of_measurement;J=device_class;I=device_type;G=discovery_topic;B('Publishing discovery packet for '+name);A={U:name,'state_topic':C.pico_id+R+P,'availability':[{'topic':C.pico_id+N,'payload_available':T,'payload_not_available':S}],'device':{'identifiers':C.pico_id,U:C.device_name,'manufacturer':'MakerLab','model':'RPI Pico W MLHA','sw_version':'0.2','connections':[['ip',C.wlan.ifconfig()[0]],[Z,L.hexlify(C.wlan.config(Z)).decode()]]},'unique_id':C.pico_id+'-'+G,V:J,W:'{{ value_json.'+G+' }}',X:M,Y:Q,'expire_after':expire_after}
		if R!=O:del A[W]
		if J is D:del A[V]
		if M is D:del A[X]
		if Q is D:del A[Y]
		if I=='binary_sensor':
			A[a]=E;A[b]=F
			if J is'connectivity':A['entity_category']='diagnostic'
		if I=='switch':A['command_topic']=C.pico_id+'/switch/toggle/'+G;A[a]=E;A[b]=F;A['state_on']=E;A['state_off']=F;A['icon']='mdi:power'
		C.mqtt.publish('homeassistant/'+I+H+C.pico_id+H+G+'/config',K.dumps(A),retain=E)
	def publish_status(A,status_data):
		A.led.on()
		if not A.mqtt.is_keepalive():B('MQTT not connected, skipping');return
		C=K.dumps(status_data);A.mqtt.publish(A.pico_id+N,T,retain=E);A.mqtt.publish(A.pico_id+P,C);A.led.off()
	def check_mqtt_msg(A):
		try:
			if A.mqtt.is_keepalive():A.mqtt.check_msg();A.mqtt.send_queue()
		except Exception as D:B('error: '+C(D));G.reset()