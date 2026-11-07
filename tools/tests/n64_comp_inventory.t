use strict;
use warnings;
use Test::More;
use File::Temp qw(tempfile);
use FindBin qw($Bin);
use File::Spec;
use IPC::Open3;
use Symbol qw(gensym);

my $script = File::Spec->catfile($Bin, '..', 'n64_comp_inventory.pl');

sub write_temp {
    my ($bytes) = @_;
    my ($fh, $path) = tempfile();
    binmode $fh;
    print {$fh} $bytes or die "cannot write test fixture: $!";
    close $fh or die "cannot close test fixture: $!";
    return $path;
}

sub run_scanner {
    my ($bytes) = @_;
    my $pad = @_ > 1 ? $_[1] : "\0";
    $bytes .= $pad while length($bytes) % 4;
    my $path = write_temp($bytes);
    my $stderr = gensym();
    my $pid = open3(undef, my $stdout, $stderr, $^X, $script, $path);
    local $/;
    my $output = <$stdout> // '';
    my $errors = <$stderr> // '';
    waitpid($pid, 0);
    my $status = $? >> 8;
    close $stdout;
    close $stderr;
    unlink $path;
    return ($status, $output . $errors);
}

sub n64_header { return "\x80\x37\x12\x40" . ("\0" x 60); }
sub compwolf_block {
    my ($expected, $stream) = @_;
    return "CompWolf" . pack('N', $expected) . $stream;
}

# Four literal output bytes, followed by the two-byte zero-offset terminator.
my $literal_block = compwolf_block(4, pack('C*', 0x0F) . 'Pupp' . pack('C*', 0, 0));
my ($status, $out) = run_scanner(n64_header() . "Company LLC\0" . $literal_block);
is($status, 0, 'literal-only CompWolf record is accepted');
like($out, qr/Raw ASCII 'Comp' occurrences:\s+2/, 'raw Comp marker count includes a false textual hit');
like($out, qr/Validated CompWolf records:\s+1/, 'only the exact CompWolf record is counted');
like($out, qr/Decoded-size sum .*:\s+4 bytes/, 'decoded length is counted from tokens');
like($out, qr/Pupp:\s+1/, 'first decoded four-byte tag is reported');
like($out, qr/Offset\s+Tag/s, 'record metadata table is emitted');

# Five literals fill history slots 1..5. The first copy reads slot 5 and
# overlaps its own output at slot 6; it must not be flagged as an unknown read.
my $overlap_stream = pack('C*', 0x1F) . "Pupp\0" . pack('C*', 0, 5, 0, 0);
my $overlap_block = compwolf_block(7, $overlap_stream);
($status, $out) = run_scanner(n64_header() . $overlap_block);
is($status, 0, 'overlapping back-reference sample is accepted');
like($out, qr/Decoded-size sum .*:\s+7 bytes/, 'overlapping copy length is accounted for');
like($out, qr/Undefined initial-history reads:\s+0/, 'overlapping copy reads its just-written history slot');

# A first token that references an unwritten history slot is counted but
# surfaced explicitly; the scanner never invents an initial dictionary value.
my $seed_stream = pack('C*', 0x00, 0, 5, 0, 0);
my $seed_block = compwolf_block(2, $seed_stream);
($status, $out) = run_scanner(n64_header() . $seed_block);
is($status, 0, 'structurally valid stream with initial-window dependency is counted');
like($out, qr/Undefined initial-history reads:\s+2/, 'undefined dictionary reads are explicitly reported');

# Reject a stream whose declared output size does not match token output.
my $bad_length = compwolf_block(5, pack('C*', 0x0F) . 'Pupp' . pack('C*', 0, 0));
($status, $out) = run_scanner(n64_header() . $bad_length);
isnt($status, 0, 'decoded-size mismatch is not accepted');
like($out, qr/Rejected CompWolf candidates:\s+1/, 'malformed candidate is reported');
like($out, qr/decoded length mismatch/, 'mismatch reason is visible');

# Truncated stream is rejected safely.
my $truncated = compwolf_block(4, pack('C*', 0x0F) . 'Pupp');
($status, $out) = run_scanner(n64_header() . $truncated, "\xFF");
isnt($status, 0, 'missing terminator is not accepted');
like($out, qr/missing zero-offset stream terminator|truncated back-reference token|decoded length exceeds header/, 'truncation reason is reported');

# Byte-swapped N64 images are normalized before scanning.
my $v64 = n64_header() . $literal_block;
$v64 .= "\0" while length($v64) % 4;
my $v64_all = $v64;
$v64_all =~ s/(.)(.)/$2$1/sg;
($status, $out) = run_scanner($v64_all);
is($status, 0, 'v64 byte-swapped image is normalized');
like($out, qr/Byte order: v64-normalized/, 'v64 normalization is identified');

my $n64_all = $v64;
$n64_all =~ s/(....)/reverse($1)/sge;
($status, $out) = run_scanner($n64_all);
is($status, 0, 'n64 word-swapped image is normalized');
like($out, qr/Byte order: n64-normalized/, 'n64 normalization is identified');

done_testing();
