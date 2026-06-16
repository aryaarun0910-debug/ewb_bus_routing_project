module latencyZeroFPGA (
    input  logic        CLOCK_50,
    input  logic [3:0]  KEY,
    input  logic [9:0]  SW,
    inout  wire  [35:0] GPIO_0,
    output logic [9:0]  LEDR,
    output logic [6:0]  HEX0, HEX1, HEX2, HEX3, HEX4, HEX5
);

wire clk   = CLOCK_50;
wire rst_n = KEY[0];

// -- Demand ROM (direct from bus_route.v) ------------------------------------
// 60-bit packed rows: 15 stops x 4-bit demand, MSB = stop 0
function [3:0] demand_rom;
    input [4:0] addr;
    input [3:0] stop;
    reg [59:0] row;
    begin
        case (addr)
            5'd 0: row = 60'h645588655844888; // Sunny Early Morning
            5'd 1: row = 60'h757698767866988; // Sunny AM Peak
            5'd 2: row = 60'h786648756855888; // Sunny Mid Morning
            5'd 3: row = 60'h786548656855888; // Sunny Lunch
            5'd 4: row = 60'h787648767865888; // Sunny Afternoon
            5'd 5: row = 60'h747688767866888; // Sunny PM Peak
            5'd 6: row = 60'h787648767865888; // Sunny Evening
            5'd 7: row = 60'h645500655044800; // Sunny Night
            5'd 8: row = 60'h686548655854888; // Rain Early Morning
            5'd 9: row = 60'h797659767866989; // Rain AM Peak
            5'd10: row = 60'h747688766855888; // Rain Mid Morning
            5'd11: row = 60'h746588756855888; // Rain Lunch
            5'd12: row = 60'h747688767866888; // Rain Afternoon
            5'd13: row = 60'h747688767866888; // Rain PM Peak
            5'd14: row = 60'h787648767866888; // Rain Evening
            5'd15: row = 60'h646588656054808; // Rain Night
            5'd16: row = 60'h685540645844808; // Festival Early Morning
            5'd17: row = 60'h787588756855444; // Festival AM Peak
            5'd18: row = 60'h746588756855888; // Festival Mid Morning
            5'd19: row = 60'h747588656855800; // Festival Lunch
            5'd20: row = 60'h747688757855888; // Festival Afternoon
            5'd21: row = 60'h747688757855808; // Festival PM Peak
            5'd22: row = 60'h787648756055808; // Festival Evening
            5'd23: row = 60'h706540656054800; // Festival Night
            5'd24: row = 60'h645588555844888; // Storm Early Morning
            5'd25: row = 60'h797658767866988; // Storm AM Peak
            5'd26: row = 60'h686548656855888; // Storm Mid Morning
            5'd27: row = 60'h646588656855888; // Storm Lunch
            5'd28: row = 60'h747688766855888; // Storm Afternoon
            5'd29: row = 60'h787648766855888; // Storm PM Peak
            5'd30: row = 60'h746688766855888; // Storm Evening
            5'd31: row = 60'h545400544044400; // Storm Night
            default: row = 60'h0;
        endcase
        case (stop)
            4'd 0: demand_rom = row[59:56];
            4'd 1: demand_rom = row[55:52];
            4'd 2: demand_rom = row[51:48];
            4'd 3: demand_rom = row[47:44];
            4'd 4: demand_rom = row[43:40];
            4'd 5: demand_rom = row[39:36];
            4'd 6: demand_rom = row[35:32];
            4'd 7: demand_rom = row[31:28];
            4'd 8: demand_rom = row[27:24];
            4'd 9: demand_rom = row[23:20];
            4'd10: demand_rom = row[19:16];
            4'd11: demand_rom = row[15:12];
            4'd12: demand_rom = row[11:8];
            4'd13: demand_rom = row[7:4];
            4'd14: demand_rom = row[3:0];
            default: demand_rom = 4'h0;
        endcase
    end
endfunction

// -- UART RX (Pi -> FPGA) ----------------------------------------------------
logic [7:0] rx_data;
logic       rx_valid;

uart_rx u_rx (
    .clk   (clk),
    .rst_n (rst_n),
    .rx    (GPIO_0[0]),
    .data  (rx_data),
    .valid (rx_valid)
);

// -- Frame parser ------------------------------------------------------------
logic [7:0] stop_regs [0:14];
logic       frame_valid;

frame_rx u_frame (
    .clk        (clk),
    .rst_n      (rst_n),
    .rx_data    (rx_data),
    .rx_valid   (rx_valid),
    .stop_regs  (stop_regs),
    .frame_valid(frame_valid)
);

// -- Button debounce (20 ms, active-low KEY) ----------------------------------
localparam DB = 20'd1_000_000;

logic [19:0] db1, db2, db3;
logic        st1, st2, st3;
logic        key1_p, key2_p, key3_p;
logic        k1s, k2s, k3s;

always_ff @(posedge clk) begin k1s <= KEY[1]; k2s <= KEY[2]; k3s <= KEY[3]; end

always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin db1<='0; st1<=1'b1; key1_p<=1'b0; end
    else begin
        key1_p <= 1'b0;
        if      (k1s == st1) db1 <= '0;
        else if (db1 < DB)   db1 <= db1 + 1;
        else begin st1 <= k1s; db1 <= '0; if (!k1s) key1_p <= 1'b1; end
    end
end

always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin db2<='0; st2<=1'b1; key2_p<=1'b0; end
    else begin
        key2_p <= 1'b0;
        if      (k2s == st2) db2 <= '0;
        else if (db2 < DB)   db2 <= db2 + 1;
        else begin st2 <= k2s; db2 <= '0; if (!k2s) key2_p <= 1'b1; end
    end
end

always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin db3<='0; st3<=1'b1; key3_p<=1'b0; end
    else begin
        key3_p <= 1'b0;
        if      (k3s == st3) db3 <= '0;
        else if (db3 < DB)   db3 <= db3 + 1;
        else begin st3 <= k3s; db3 <= '0; if (!k3s) key3_p <= 1'b1; end
    end
end

// -- Auto-tick state machine --------------------------------------------------
localparam TICK_SLOW = 31'd1_500_000_000;
localparam TICK_FAST = 31'd  150_000_000;

logic [30:0] tick_cnt;
logic [2:0]  auto_ts;
logic [1:0]  auto_sc;

wire [30:0] tick_limit = SW[8] ? TICK_FAST : TICK_SLOW;

always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        tick_cnt <= '0; auto_ts <= 3'd0; auto_sc <= 2'd0;
    end else begin
        if (key1_p) begin
            tick_cnt <= '0;
            if (auto_ts == 3'd7) begin auto_ts <= 3'd0; auto_sc <= auto_sc + 1; end
            else                        auto_ts <= auto_ts + 1;
        end else if (key2_p) begin
            tick_cnt <= '0;
            if (auto_ts == 3'd0) begin auto_ts <= 3'd7; auto_sc <= auto_sc - 1; end
            else                        auto_ts <= auto_ts - 1;
        end else if (key3_p) begin
            auto_sc <= auto_sc + 1; tick_cnt <= '0;
        end else if (SW[9]) begin
            if (tick_cnt >= tick_limit - 1) begin
                tick_cnt <= '0;
                if (auto_ts == 3'd7) begin auto_ts <= 3'd0; auto_sc <= auto_sc + 1; end
                else                        auto_ts <= auto_ts + 1;
            end else
                tick_cnt <= tick_cnt + 1;
        end
    end
end

wire [1:0] eff_sc  = SW[9] ? auto_sc : SW[1:0];
wire [2:0] eff_ts  = SW[9] ? auto_ts : SW[4:2];
wire [4:0] rom_idx = {eff_sc, eff_ts};

// -- Output frame (combinational) --------------------------------------------
logic [7:0] out_payload [0:14];
logic [7:0] out_csum;

genvar gi;
generate
    for (gi = 0; gi < 15; gi++) begin : gen_payload
        assign out_payload[gi] = {stop_regs[gi][7:4], demand_rom(rom_idx, gi)};
    end
endgenerate

assign out_csum = out_payload[0]  ^ out_payload[1]  ^ out_payload[2]  ^
                  out_payload[3]  ^ out_payload[4]  ^ out_payload[5]  ^
                  out_payload[6]  ^ out_payload[7]  ^ out_payload[8]  ^
                  out_payload[9]  ^ out_payload[10] ^ out_payload[11] ^
                  out_payload[12] ^ out_payload[13] ^ out_payload[14];

// -- UART TX (FPGA -> Pi) ----------------------------------------------------
logic uart_tx_wire, tx_start_sig, tx_busy_sig;
logic [7:0] tx_data_sig;

uart_tx u_tx (
    .clk   (clk), .rst_n (rst_n),
    .data  (tx_data_sig), .start (tx_start_sig),
    .tx    (uart_tx_wire), .busy  (tx_busy_sig)
);
assign GPIO_0[1] = uart_tx_wire;

// -- TX FSM ------------------------------------------------------------------
logic [7:0] tx_buf [0:16];
logic [4:0] tx_idx;
logic       tx_sending;

always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        tx_sending <= 1'b0; tx_idx <= '0;
        tx_start_sig <= 1'b0; tx_data_sig <= '0;
        for (int i = 0; i < 17; i++) tx_buf[i] <= '0;
    end else begin
        tx_start_sig <= 1'b0;
        if (frame_valid && !tx_sending) begin
            tx_buf[0] <= 8'hBB;
            for (int i = 0; i < 15; i++) tx_buf[i+1] <= out_payload[i];
            tx_buf[16] <= out_csum;
            tx_idx <= '0; tx_sending <= 1'b1;
        end
        if (tx_sending && !tx_busy_sig && !tx_start_sig) begin
            tx_data_sig  <= tx_buf[tx_idx];
            tx_start_sig <= 1'b1;
            if (tx_idx == 5'd16) tx_sending <= 1'b0;
            else                 tx_idx <= tx_idx + 1;
        end
    end
end

// -- Staleness watchdog ------------------------------------------------------
logic [31:0] stale_cnt;
logic        stale, live;
logic [25:0] blink_cnt;

always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n)                              begin stale_cnt<='0; stale<=1'b0; end
    else if (frame_valid)                    begin stale_cnt<='0; stale<=1'b0; end
    else if (stale_cnt < 32'd3_000_000_000) stale_cnt <= stale_cnt + 1;
    else                                     stale <= 1'b1;
end

always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) blink_cnt <= '0; else blink_cnt <= blink_cnt + 1;
end

always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n)           live <= 1'b0;
    else if (frame_valid) live <= 1'b1;
    else if (stale)       live <= 1'b0;
end

// -- LEDR --------------------------------------------------------------------
// generate/assign instead of always_comb: Quartus synthesises function calls
// in generate blocks reliably; always_comb loop was producing constant 0.
genvar li;
generate
    for (li = 0; li < 9; li++) begin : gen_ledr
        assign LEDR[li] = (demand_rom(rom_idx, li[3:0]) > 4'h0);
    end
endgenerate
assign LEDR[9] = stale & blink_cnt[25];

// -- 7-seg -------------------------------------------------------------------
function automatic [6:0] seg7(input [3:0] d);
    case (d)
        4'd0: seg7=7'b1000000; 4'd1: seg7=7'b1111001; 4'd2: seg7=7'b0100100;
        4'd3: seg7=7'b0110000; 4'd4: seg7=7'b0011001; 4'd5: seg7=7'b0010010;
        4'd6: seg7=7'b0000010; 4'd7: seg7=7'b1111000; 4'd8: seg7=7'b0000000;
        default: seg7=7'b1111111;
    endcase
endfunction

localparam SEG_A=7'b0001000, SEG_F=7'b0001110, SEG_DASH=7'b0111111, SEG_L=7'b1000111;

logic [3:0] h_tens, h_units;
always_comb begin
    case (eff_ts)
        3'd0: begin h_tens=4'd0; h_units=4'd6; end
        3'd1: begin h_tens=4'd0; h_units=4'd8; end
        3'd2: begin h_tens=4'd1; h_units=4'd0; end
        3'd3: begin h_tens=4'd1; h_units=4'd2; end
        3'd4: begin h_tens=4'd1; h_units=4'd4; end
        3'd5: begin h_tens=4'd1; h_units=4'd6; end
        3'd6: begin h_tens=4'd1; h_units=4'd8; end
        3'd7: begin h_tens=4'd2; h_units=4'd0; end
        default: begin h_tens=4'd0; h_units=4'd0; end
    endcase
end

assign HEX0 = seg7(h_units);
assign HEX1 = seg7(h_tens);
assign HEX2 = seg7({2'b00, eff_sc});
assign HEX3 = SW[9] ? (SW[8] ? SEG_F : SEG_A) : SEG_DASH;
assign HEX4 = live ? SEG_L : SEG_DASH;
assign HEX5 = 7'b1111111;

endmodule
