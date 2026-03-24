# BMP180_Raspberry
Codice per verificare il funzionamento e implementare il sensore BMP180 con Raspberry usando Python

Viene utilizzata la libreria smbus3, per instalarla seguire i seguenti passaggi:
- eseguire il comando su bash: sudo apt install -y python3-smbus i2c-tools python3-pip
- eseguire il comando su bash: pip3 install smbus3
- collegare il sensore ed eseguire il comando su bash: i2cdetect -y 1 per verificare che sia connesso correttamente
- prelevare il codice allegato e testarne il funzionamento
