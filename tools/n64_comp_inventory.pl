#!/usr/bin/perl
use strict;
use warnings;
use File::Basename qw(basename);

# Read-only metadata inventory for N64 CompWolf records.
# No decoded bytes or game assets are written to disk or printed.
# This is an independently written structural reader; it does not copy the
# GPL-2.0-or-later swe1r-tools decompressor.

use constant {
    HEADER_SIZE       => 12,
    MAX_OUTPUT_SIZE   => 256 * 1024 * 1024,
    MAGIC_COMP_WOLF   => "CompWolf",
};

sub usage {
    die "Usage: perl n64_comp_inventory.pl /path/to/local-rom.z64\n";
}

@ARGV == 1 or usage();
my $path = $ARGV[0];
open my $fh, '<:raw', $path or die "ERROR: cannot read '$path': $!\n";
my $data = do { local $/; <$fh> };
close $fh or die "ERROR: could not close input: $!\n";
defined $data or die "ERROR: input is empty or unreadable\n";

my $rom_size = length($data);
$rom_size >= 4 or die "ERROR: file is too short to contain an N64 header\n";
my $magic = substr($data, 0, 4);
my $byte_order;
if ($magic eq "\x80\x37\x12\x40") {
    $byte_order = 'z64-big-endian';
} elsif ($magic eq "\x37\x80\x40\x12") {
    length($data) % 2 == 0 or die "ERROR: v64 image has an incomplete 16-bit byte-swap pair\n";
    $data =~ s/(.)(.)/$2$1/sg;
    $byte_order = 'v64-normalized';
} elsif ($magic eq "\x40\x12\x37\x80") {
    length($data) % 4 == 0 or die "ERROR: n64 image has an incomplete 32-bit byte-swap word\n";
    $data =~ s/(....)/reverse($1)/sge;
    $byte_order = 'n64-normalized';
} else {
    die "ERROR: unrecognized N64 byte-order magic; expected z64, v64 or n64\n";
}

sub comma {
    my ($n) = @_;
    1 while $n =~ s/^(-?\d+)(\d{3})/$1,$2/;
    return $n;
}

# Read just enough token metadata to establish the chunk boundary, decoded
# output length and first four decoded bytes. A 4 KiB shadow history tracks
# whether source bytes have been defined, including legal overlapping copies.
# Unknown initial-window reads are reported, never silently zero-filled.
sub inspect_chunk {
    my ($bytes, $start) = @_;
    my $size = length($bytes);
    return (undef, 'truncated 12-byte header') if $start + HEADER_SIZE > $size;

    my $expected = unpack('N', substr($bytes, $start + 8, 4));
    return (undef, 'zero decoded-size field') if $expected == 0;
    return (undef, 'decoded-size exceeds safety limit') if $expected > MAX_OUTPUT_SIZE;

    my $input = $start + HEADER_SIZE;
    my $produced = 0;
    my $write_index = 1;
    my @history;
    my $unknown_history_reads = 0;
    my @prefix;

    while ($input < $size) {
        my $control = ord(substr($bytes, $input, 1));
        $input++;

        for my $bit (0 .. 7) {
            if ($control & (1 << $bit)) {
                return (undef, 'truncated literal token') if $input >= $size;
                my $value = ord(substr($bytes, $input, 1));
                $input++;
                push @prefix, $value if @prefix < 4;
                $history[$write_index] = $value;
                $write_index = ($write_index + 1) & 0xFFF;
                $produced++;
            } else {
                return (undef, 'truncated back-reference token') if $input + 2 > $size;
                my $b1 = ord(substr($bytes, $input, 1));
                my $b2 = ord(substr($bytes, $input + 1, 1));
                $input += 2;
                my $source = (($b1 & 0x0F) << 8) | $b2;
                my $length = (($b1 >> 4) & 0x0F) + 2;

                if ($source == 0) {
                    return (undef, 'decoded length exceeds header') if $produced > $expected;
                    return (undef, "decoded length mismatch (header=$expected, stream=$produced)")
                        if $produced != $expected;
                    my $prefix_known = @prefix == 4;
                    $prefix_known = 0 if grep { !defined $_ } @prefix;
                    my $tag = $prefix_known ? pack('C*', @prefix) : undef;
                    return ({
                        start                   => $start,
                        end                     => $input,
                        compressed_stream_bytes => $input - ($start + HEADER_SIZE),
                        rom_span_bytes           => $input - $start,
                        decoded_bytes            => $produced,
                        output_tag               => $tag,
                        unknown_history_reads    => $unknown_history_reads,
                    }, undef);
                }

                for my $copy_index (0 .. $length - 1) {
                    my $source_index = ($source + $copy_index) & 0xFFF;
                    my $value = $history[$source_index];
                    $unknown_history_reads++ if !defined $value;
                    push @prefix, $value if @prefix < 4;
                    $history[$write_index] = $value;
                    $write_index = ($write_index + 1) & 0xFFF;
                    $produced++;
                    return (undef, 'decoded length exceeds header') if $produced > $expected;
                }
            }
        }
    }
    return (undef, 'missing zero-offset stream terminator');
}

my $raw_comp_count = 0;
my $raw_at = 0;
while (1) {
    my $hit = index($data, 'Comp', $raw_at);
    last if $hit < 0;
    $raw_comp_count++;
    $raw_at = $hit + 1;
}

my @records;
my @rejected;
my $cursor = 0;
while (1) {
    my $offset = index($data, MAGIC_COMP_WOLF, $cursor);
    last if $offset < 0;
    my ($record, $error) = inspect_chunk($data, $offset);
    if ($record) {
        push @records, $record;
        # Skip the validated compressed payload, so marker-like bytes inside a
        # compressed stream are not double-counted as separate records.
        $cursor = $record->{end};
    } else {
        push @rejected, { offset => $offset, reason => $error };
        $cursor = $offset + 1;
    }
}

my %tag_counts;
my ($decoded_total, $stream_total, $span_total, $history_reads) = (0, 0, 0, 0);
for my $record (@records) {
    my $tag = defined($record->{output_tag}) ? $record->{output_tag} : '????';
    $tag =~ s/[^\x20-\x7E]/./g;
    $tag_counts{$tag}++;
    $decoded_total += $record->{decoded_bytes};
    $stream_total += $record->{compressed_stream_bytes};
    $span_total += $record->{rom_span_bytes};
    $history_reads += $record->{unknown_history_reads};
}

print "N64 CompWolf metadata inventory (read-only; no asset extraction)\n";
print "File: ", basename($path), "\n";
print "ROM size: ", comma($rom_size), " bytes\n";
print "Byte order: $byte_order\n";
print "Raw ASCII 'Comp' occurrences: ", comma($raw_comp_count), "\n";
print "Validated CompWolf records: ", comma(scalar @records), "\n";
print "Rejected CompWolf candidates: ", comma(scalar @rejected), "\n";
print "Decoded-size sum (header-validated): ", comma($decoded_total), " bytes\n";
print "Compressed stream bytes (including terminators): ", comma($stream_total), " bytes\n";
print "ROM span bytes (12-byte headers + streams): ", comma($span_total), " bytes\n";
print "Undefined initial-history reads: ", comma($history_reads), "\n";
print "Output-tag counts (first four decoded bytes only):\n";
for my $tag (sort keys %tag_counts) {
    print "  $tag: ", comma($tag_counts{$tag}), "\n";
}
print "\nRecord metadata (no ROM/decompressed bytes):\n";
print "Offset       Tag    Header-size  Decoded-size  Stream-bytes  ROM-span  History-reads\n";
for my $record (@records) {
    my $tag = defined($record->{output_tag}) ? $record->{output_tag} : '????';
    $tag =~ s/[^\x20-\x7E]/./g;
    printf "0x%08X  %-4s  %11s  %12s  %12s  %8s  %13s\n",
        $record->{start}, $tag, comma(HEADER_SIZE), comma($record->{decoded_bytes}),
        comma($record->{compressed_stream_bytes}), comma($record->{rom_span_bytes}),
        comma($record->{unknown_history_reads});
}
if (@rejected) {
    print "\nRejected candidate offsets/reasons:\n";
    for my $item (@rejected) {
        printf "0x%08X  %s\n", $item->{offset}, $item->{reason};
    }
}
print "\nInterpretation: this is structural metadata only. It does not establish\n";
print "that records are route splines, validate a GameCube conversion, or grant\n";
print "rights to redistribute any ROM-derived data or assets.\n";
exit(@records ? 0 : 2);
