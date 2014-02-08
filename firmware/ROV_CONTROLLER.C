// UWM ROV Team Controller 2008
//*****************************
#define DEBUG_MSG 1
#define TCPCONFIG 0
#define MY_IP_ADDRESS "192.168.1.222"
#define MY_NETMASK "255.255.255.0"
//#define MY_GATEWAY "10.10.6.19"
#define LOCAL_PORT   22222
#memmap xmem
#define USE_ETHERNET 1
#use "dcrtcp.lib"
#define EINBUFSIZE 31
#define EOUTBUFSIZE 31
//*****************************
//Defines for easy reading
#define RH 0 //LH (Left Horizontal) Thruster
#define LH 1 //RH (Right Horizontal) Thruster
#define RV 2 //LV (Left Vertical) Thruster
#define LV 3 //RV (Right Vertical) Thruster
//*****************************
//Constants
const int CONTROL_PACKET_SIZE = 8;
const char atod_cmd[] = "VA\r";
//*****************************
//Global Variables
char server_buffer[8];
int local_buffer[8];
int bytes_read;
int return_value;
int i;
tcp_Socket server_socket;  //The socket to use for TCP communications.
//*****************************
//Function declarations
int connection_established();
int check_for_received_data();
void service_request();
void measure_temp();
void move(int servo, int pos);
void move_thrusters(int srv1, int pwm1, int srv2, int pwm2);

//*****************************
// Pin number		pin name		function
// 30					PG7			RX2 - RXE
// 31					PG6			TX2 - TXE
//*****************************
main()
{
	//Initialize Port G for Serial TX to all outputs (may need to change for RX)
	WrPortI(PGDR, &PGDRShadow,0x00);
	//Set Port G function register for Serial TX (PG6)
	WrPortI(PGFR, &PGFRShadow,0x40);
	//Set port G to all outputs
	WrPortI(PGDDR, &PGDDRShadow, 0x7F);
	serEopen(115200);

   //initalize local values to values outside of valid range
   for(i=0; i < CONTROL_PACKET_SIZE; i++)
   {
    	local_buffer[i] = 255;
   }
   // sock_init must be called before using other functions in dcrtcp.lib.
   // If the return value isn't zero, the network isn't available.
   if (sock_init() == 0)
   {
      // Listen for a connection request on the specified local port.
      tcp_listen(&server_socket,LOCAL_PORT,0,0,NULL,0);
      printf("Waiting for connection...\n");

      while(1) // Endless loop.
      {
			costate
         {
            waitfor (connection_established());
            printf("Connection established. \n");

            waitfor (check_for_received_data() || DelaySec(20));

            // Find out if data has been received.
            // If data has been received, service the request.
            if (check_for_received_data() > 0)
            {
               service_request();
            }
         } // end: costate
      	costate // Recieve and send temp
      	{
      		waitfor(DelaySec(1));
         	measure_temp();
      	}

      } // end: while(1)
   } // end: sock_init() == 0
   else // The call to sock_init failed.
   {
      printf("The network is not available. \n");
      exit(0);
   }
   // The communications are complete, so close the connection.
   sock_close(&server_socket);
	printf("The connection is closed. \n");
} // end: main

int connection_established()
{
   // Return 1 if a connection has been established or if the socket is closed
   // but there are one or more bytes waiting to be read.
   tcp_tick(NULL);
   if (!sock_established(&server_socket) && sock_bytesready(&server_socket) == -1)
   	return 0;
   else
   	return 1;
}

int check_for_received_data()
{
   // Process network packets on the TCP socket.
   tcp_tick(&server_socket);
   // Return 1 if there is a byte waiting to be read.
   if (sock_bytesready(&server_socket) < 0)
   	return 0;
   else
   	return 1;
}

void service_request()
{
   // Attempt to read a received byte.
   bytes_read = sock_fastread(&server_socket,server_buffer,8);
   if (bytes_read > 0)
   {
	/*
	   printf("Bytes read is: %d\n",bytes_read);
          for (i=0;i<bytes_read;++i)
          {
            printf("%d,",server_buffer[i]);
            //sock_write(&server_socket,array,5);
          }
          putchar('\n');
	*/
          if (server_buffer[1] != local_buffer[1]
	      	|| server_buffer[2] != local_buffer[2])
          {
         	local_buffer[1] = server_buffer[1];
				local_buffer[2] = server_buffer[2];
            //printf("buffer[1]: %d \nbuffer[2]: %d\n",
            //			server_buffer[1], server_buffer[2]);
            move_thrusters(LV, server_buffer[1], RV, server_buffer[2]);
          }
         if (server_buffer[3] != local_buffer[3]
         	|| server_buffer[4] != local_buffer[4])
         {
         	local_buffer[3] = server_buffer[3];
				local_buffer[4] = server_buffer[4];
            //printf("buffer[3]: %d \nbuffer[4]: %d\n",
            //			server_buffer[3], server_buffer[4]);
            move_thrusters(LH, server_buffer[3], RH, server_buffer[4]);
         }
         if (server_buffer[5] != local_buffer[5])
         {
         	local_buffer[5] = server_buffer[5];
            move(ARM, server_buffer[5]);
         }
   }  // end: if (bytes_read > 0)
   else printf("Error reading from socket. \n");
} // end: service_request


void measure_temp()
{
   serEputs(atod_cmd);
	return_value = serEgetc();
   printf("VA = %d\n", return_value);
   if (connection_established() == 1)
   {
   	sock_putc(&server_socket, 255);
   	sock_putc(&server_socket, return_value);
   }
}

void move(int servo, int pos)
{
	char cmd[8];
   sprintf(cmd, "#%dP%d0\r", servo, pos);
   printf("move servo: %s\n", cmd);
   serEputs(cmd);
}

// @pre: motors 1-4; pwm between 90-210
void move_thrusters(int motor1, int pwm1, int motor2, int pwm2) {
	char cmd[16];
   sprintf(cmd, "#%dP%d0#%dP%d0\r", motor1, pwm1, motor2, pwm2);
	printf("move thrusters: %s\n", cmd);
   serEputs(cmd);
}

