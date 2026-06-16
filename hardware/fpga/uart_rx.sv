module uart_rx (
    input  logic       clk,
    input  logic       rst_n,
    input  logic       rx,
    output logic [7:0] data,
    output logic       valid
);

localparam CLKS_PER_BIT = 5208;  // 50 MHz / 9600 baud

// 2-FF synchroniser â€” treats rx as async input
logic rx_s1, rx_sync;
always_ff @(posedge clk) begin
    rx_s1  <= rx;
    rx_sync <= rx_s1;
end

typedef enum logic [1:0] {IDLE, START, DATA, STOP} state_t;
state_t state;

logic [12:0] clk_cnt;
logic [2:0]  bit_cnt;
logic [7:0]  shift_reg;

always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        state     <= IDLE;
        clk_cnt   <= '0;
        bit_cnt   <= '0;
        shift_reg <= '0;
        data      <= '0;
        valid     <= 1'b0;
    end else begin
        valid <= 1'b0;

        case (state)
            IDLE: begin
                if (!rx_sync)
                    state <= START;
            end

            START: begin
                if (clk_cnt == CLKS_PER_BIT/2 - 1) begin
                    clk_cnt <= '0;
                    state   <= rx_sync ? IDLE : DATA;
                    bit_cnt <= '0;
                end else begin
                    clk_cnt <= clk_cnt + 1;
                end
            end

            DATA: begin
                if (clk_cnt == CLKS_PER_BIT - 1) begin
                    clk_cnt   <= '0;
                    shift_reg <= {rx_sync, shift_reg[7:1]};
                    if (bit_cnt == 7)
                        state <= STOP;
                    else
                        bit_cnt <= bit_cnt + 1;
                end else begin
                    clk_cnt <= clk_cnt + 1;
                end
            end

            STOP: begin
                if (clk_cnt == CLKS_PER_BIT - 1) begin
                    clk_cnt <= '0;
                    state   <= IDLE;
                    if (rx_sync) begin
                        data  <= shift_reg;
                        valid <= 1'b1;
                    end
                end else begin
                    clk_cnt <= clk_cnt + 1;
                end
            end
        endcase
    end
end

endmodule
