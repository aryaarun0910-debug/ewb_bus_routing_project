
module uart_tx (
    input  logic       clk,
    input  logic       rst_n,
    input  logic [7:0] data,
    input  logic       start,
    output logic       tx,
    output logic       busy
);

localparam CLKS_PER_BIT = 5208;  // 50 MHz / 9600 baud

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
        tx        <= 1'b1;
        busy      <= 1'b0;
    end else begin
        case (state)
            IDLE: begin
                tx   <= 1'b1;
                busy <= 1'b0;
                if (start) begin
                    shift_reg <= data;
                    state     <= START;
                    clk_cnt   <= '0;
                    busy      <= 1'b1;
                end
            end

            START: begin
                tx <= 1'b0;
                if (clk_cnt == CLKS_PER_BIT - 1) begin
                    clk_cnt <= '0;
                    bit_cnt <= '0;
                    state   <= DATA;
                end else begin
                    clk_cnt <= clk_cnt + 1;
                end
            end

            DATA: begin
                tx <= shift_reg[0];
                if (clk_cnt == CLKS_PER_BIT - 1) begin
                    clk_cnt   <= '0;
                    shift_reg <= {1'b0, shift_reg[7:1]};
                    if (bit_cnt == 7)
                        state <= STOP;
                    else
                        bit_cnt <= bit_cnt + 1;
                end else begin
                    clk_cnt <= clk_cnt + 1;
                end
            end

            STOP: begin
                tx <= 1'b1;
                if (clk_cnt == CLKS_PER_BIT - 1) begin
                    clk_cnt <= '0;
                    state   <= IDLE;
                end else begin
                    clk_cnt <= clk_cnt + 1;
                end
            end
        endcase
    end
end

endmodule