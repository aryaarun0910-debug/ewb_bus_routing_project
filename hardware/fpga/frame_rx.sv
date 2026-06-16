module frame_rx (
    input  logic        clk,
    input  logic        rst_n,
    input  logic [7:0]  rx_data,
    input  logic        rx_valid,
    output logic [7:0]  stop_regs[0:14],   // S01â€“S15, one byte each
    output logic        frame_valid         // pulses high 1 cycle on good frame
);

typedef enum logic [1:0] {WAIT_SYNC, RECV_DATA, RECV_CHK} state_t;
state_t state;

logic [7:0] buf_regs[0:14];
logic [7:0] checksum;
logic [3:0] byte_cnt;

always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        state       <= WAIT_SYNC;
        byte_cnt    <= '0;
        checksum    <= '0;
        frame_valid <= 1'b0;
        for (int i = 0; i < 15; i++) begin
            stop_regs[i] <= '0;
            buf_regs[i]  <= '0;
        end
    end else begin
        frame_valid <= 1'b0;

        if (rx_valid) begin
            case (state)
                WAIT_SYNC: begin
                    if (rx_data == 8'hAA) begin
                        state    <= RECV_DATA;
                        byte_cnt <= '0;
                        checksum <= '0;
                    end
                end

                RECV_DATA: begin
                    buf_regs[byte_cnt] <= rx_data;
                    checksum           <= checksum ^ rx_data;
                    if (byte_cnt == 4'd14)
                        state <= RECV_CHK;
                    else
                        byte_cnt <= byte_cnt + 1;
                end

                RECV_CHK: begin
                    state <= WAIT_SYNC;
                    if (rx_data == checksum) begin
                        for (int i = 0; i < 15; i++)
                            stop_regs[i] <= buf_regs[i];
                        frame_valid <= 1'b1;
                    end
                    // bad checksum: drop silently, wait for next sync
                end
            endcase
        end
    end
end

endmodule