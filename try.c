#include <stdio.h>

int to_hex(char c) {
	if (c >= '0' && c <= '9')
		return c - '0';
	else if (c >= 'a' && c <= 'f')
		return ((c- 'a') + 10);
	else if (c >= 'A' && c <= 'F')
		return ((c- 'A') + 10);
	else
		return -1;
}

typedef struct {
    int x;
    int y;
} Position;

Position map_value_to_position(char value) {
    switch (value) {
        case 'F': return (Position){0, 0};
        case 'C': return (Position){1, 0};
        case 'A': return (Position){0, 1};
        case 'G': return (Position){1, 1};
        default:  return (Position){-1, -1};
    }
}

int le_gpio_pins[4] = {1, 2, 3, 4}; // Adjust based on your actual GPIO pin numbers
void setup_gpio() {
    pinMode(1, OUTPUT);
	pinMode(2, OUTPUT);
	pinMode(3, OUTPUT);
	pinMode(4, OUTPUT);
	pinMode(5, OUTPUT);
	pinMode(6, OUTPUT);
	pinMode(7, OUTPUT);
	pinMode(8, OUTPUT);
	pinMode(9, OUTPUT);
	pinMode(10, OUTPUT);
	pinMode(11, OUTPUT);
	pinMode(12, OUTPUT);
	pinMode(13, OUTPUT);
	Serial.begin(115200);
}

void set_channel_state(int channel, Position pos) {
    int group = channel / 4;
    int channelWithinGroup = channel % 4;

    int logicValues[2];

    // Assuming a function to apply logic values to your SP3T selector GPIO devices
    apply_logic_to_sp3t_selector(channelWithinGroup, logicValues);

    // Activate LE pin for the group
    digitalWrite(le_gpio_pins[group], HIGH);
    delayMicroseconds(3); // Adjust timing as needed
    digitalWrite(le_gpio_pins[group], LOW);
}

void setup_and_latch() {
    enable_output(HIGH);

    for (int i = 0; i < NUM_CHAN; i++) {
        // You would fill in your channel_state array based on your input processing
        Position pos = map_value_to_position(/* Assuming you have a way to get this from input */);

        set_channel_state(i, pos);
    }

    enable_output(LOW);
}



#define NUM_CHAN 16
int channel_state[NUM_CHAN];
int main(int argc, char **argv) {
	if (argc < 2) {
        printf("Usage: %s <S followed by nvnv pairs>\n", argv[0]);
        return 1;
    }

    char *input = argv[1];
	if (input[0] != 'S') {
			printf("Input must start with 'S'\n");
			return 1;
		}
    for (int i = 1; input[i] != '\0' && input[i+1] != '\0'; i += 2) {
        int channel = to_hex(input[i]);
        if (channel < 0 || channel > 15) {
            printf("Invalid channel number: %c\n", input[i]);
            continue;
        }

        Position pos = map_value_to_position(input[i + 1]);
        if (pos.x == -1 && pos.y == -1) {
            printf("Invalid position value: %c\n", input[i + 1]);
            continue;
        }
        printf("Channel %d mapped to position [%d, %d]\n", channel+1, pos.x, pos.y);
    }
    setup_gpio();
    setup_and_latch();

    return 0;
}
