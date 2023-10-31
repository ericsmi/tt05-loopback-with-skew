/*
 * tt_um_loopback_ericsmi.v
 *
 * Loopback test user module, with basic skew measurement
 *
 * Author: Eric Smith
 */

`default_nettype none
`timescale 1ns/10ps

/////////////////////////////////////////////////////////////
//`define BEHAV
/////////////////////////////////////////////////////////////
// helper modules

module buff2(input I, output Z);
`ifdef BEHAV
  assign #1 Z = I;
`else
  sky130_fd_sc_hd__buf_2 sky130_fd_sc_hd__buf_2(.A(I),.X(Z));
`endif
endmodule

module split(input I, output A,B,C);
  wire t;
  buff2 buff2(.I(I),.Z(t));
  buff2 buff2a(.I(t),.Z(A));
  buff2 buff2b(.I(t),.Z(B));
  buff2 buff2c(.I(t),.Z(C));
endmodule

module rdffe(input D,E,CLK,RSTN, output Q);
  reg FF;
  always @(negedge RSTN or posedge CLK)
    if( ~RSTN )
	  FF <= 0;
	else begin
	  if (E) FF <= D;
	end
  assign #1 Q = FF;
endmodule

module dff(input D,CLK, output Q);
  reg FF;
  always @(posedge CLK)
    FF <= D;
  assign #1 Q = FF;
endmodule

module mux8(input [7:0] I, input [2:0] S, output Z);
`ifdef BEHAV
  assign #1 Z = S[2] ? 
      ( S[1] ? ( S[0] ? I[7] : I[6] ) : ( S[0] ? I[5] : I[4] ) ): 
      ( S[1] ? ( S[0] ? I[3] : I[2] ) : ( S[0] ? I[1] : I[0] ) );
`else
  wire [1:0] w;
        sky130_fd_sc_hd__mux4_2 sky130_fd_sc_hd__mux4_2_0(
                .S1(S[1]),.S0(S[0]),
                .A0(I[0]),.A1(I[1]),.A2(I[2]),.A3(I[3]),
                .X(w[0]));
        sky130_fd_sc_hd__mux4_2 sky130_fd_sc_hd__mux4_2_1(
                .S1(S[1]),.S0(S[0]),
                .A0(I[4]),.A1(I[5]),.A2(I[6]),.A3(I[7]),
                .X(w[1]));
        sky130_fd_sc_hd__mux2_2 sky130_fd_sc_hd__mux2_2(
                .S(S[2]),
                .A0(w[0]),.A1(w[1]),
                .X(Z));
`endif
endmodule

/////////////////////////////////////////////////////////////

module tt_um_loopback_ericsmi (
	input  wire [7:0] ui_in,	// Dedicated inputs
	output wire [7:0] uo_out,	// Dedicated outputs
	input  wire [7:0] uio_in,	// IOs: Input path
	output wire [7:0] uio_out,	// IOs: Output path
	output wire [7:0] uio_oe,	// IOs: Enable path (active high: 0=input, 1=output)
	input  wire       ena,
	input  wire       clk,
	input  wire       rst_n
);

    wire [7:0] ui_ina; // for measurement
    wire [7:0] ui_inb; // for internal use, avoid loading measurement
    wire [7:0] ui_inc; // for measurement

    wire en,D,mCLK,Q,Qbypassed;

    wire default_mode_n; // when 0, match the behavior of tt05-loopback
    wire bypass;

    reg [3:0] clk_div;

    split split_ui_in [7:0] (
        .I(ui_in[7:0]),
        .A(ui_ina[7:0]), 
	.B(ui_inb[7:0]),
	.C(ui_inc[7:0]) 
    );

    rdffe rdffe_uio [7:0] (
        .D(uio_in[7:0]),
	.E({8{en}}),
        .CLK(clk),
	.RSTN({8{rst_n}}),
	.Q(uio_out[7:0])
    );

    assign bypass = uio_out[7];
    assign default_mode_n = uio_out[6];

    assign en = &ui_inb[7:4];
    assign uio_oe[7:0] = {8{~en}};

    assign uo_out[5:0] = default_mode_n ? {6{Qbypassed}} : {6{ui_inb[0]}};
    assign uo_out[6] = ui_inb[0];  // same as tt05-loopback
    assign uo_out[7] = en; // same as tt05-loopback

    // This structure does its best to keep in-tile skew the same.
    // I can't account for PnR on TT but the buffers should dominate the delay
    // and we ensure there are the same numbers and sizes of those.
    // As this tile is mostly empty I anticapte the flow should do ok at PnR. 

    mux8 mux8_d( .I(ui_ina[7:0]), .S(uio_out[2:0]), .Z(D));   
    mux8 mux8_c( .I(ui_inc[7:0]), .S(uio_out[5:3]), .Z(mCLK)); 
    
    // This is the phase measurement
    //   Start with Q=0, 
    //   Then put a rising edge on D and CLK on the outside of the IC
    //   If Q=0 then mCLK arrived before D, if Q=1 then D arrived before mCLK
    //   This allows racing inputs vs one another. 
    //   The amount of delay adjust needed on outside of the IC to make 
    //   Q toggle is the amount of skew in path from IC input pin to tile input pin. 

    dff dff( .D(D), .CLK(mCLK), .Q(Q)); 

    assign Qbypassed = bypass ? D : Q;

endmodule // tt_um_loopback
