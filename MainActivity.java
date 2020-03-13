package com.example.networks;

import android.os.StrictMode;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.util.Log;
import android.view.View;
import android.widget.Button;
import android.widget.TextView;

import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.IOException;
import java.net.InetAddress;
import java.net.Socket;
import java.net.SocketException;

public class MainActivity extends AppCompatActivity {

    private Button weatherButton;
    private TextView weatherText;
    private TextView pressureText;
    private TextView humidityText;

    private static final String HOST_NAME = "10.18.232.161";
    private static final int PORT_NUM = 12235;


    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        StrictMode.ThreadPolicy policy = new StrictMode.ThreadPolicy.Builder().permitAll().build();
        StrictMode.setThreadPolicy(policy);
        setContentView(R.layout.activity_main);
        weatherButton = findViewById(R.id.button);
        weatherText = findViewById(R.id.weatherText);
        pressureText = findViewById(R.id.pressureText);
        humidityText = findViewById(R.id.humidityText);

        weatherButton.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                updateTexts();
            }
        });
    }
 
    private void updateTexts() {
        try {
            System.out.println("fucking asshole");
            Socket tcpSocket = new Socket(InetAddress.getByName(HOST_NAME), PORT_NUM);
            System.out.println("CONNECTED");
            System.out.println(tcpSocket.isConnected());
            DataOutputStream dOut = new DataOutputStream(tcpSocket.getOutputStream());
            DataInputStream dIn = new DataInputStream(tcpSocket.getInputStream());
            byte[] checkOut = new byte[12];
            int received = dIn.read(checkOut);
            System.out.println(received);
            System.out.println("fucking asshole2");
            System.out.println(checkOut);
        } catch(IOException e) {
            e.printStackTrace();
        }
    }
}
